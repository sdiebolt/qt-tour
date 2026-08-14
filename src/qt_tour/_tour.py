from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from qtpy.QtCore import QEvent, QObject, QPoint, QRect, Qt, QTimer, Signal
from qtpy.QtGui import QColor, QFont, QKeyEvent, QPainter
from qtpy.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from qtpy.QtGui import QPaintEvent


class TourAnchor(Enum):
    """Tooltip placement relative to the target widget."""

    LEFT = "left"
    RIGHT = "right"
    ABOVE = "above"
    BELOW = "below"
    CENTER = "center"


@dataclass(frozen=True)
class TourStep:
    """One step in a guided tour.

    Parameters
    ----------
    target : Callable[[], QWidget | None]
        Callable returning the widget to highlight. Return `None` to skip the
        step until the target exists.
    title : str
        Popover title.
    body : str
        Popover body. Qt rich text is supported by `QLabel`.
    anchor : TourAnchor, default: TourAnchor.RIGHT
        Tooltip placement relative to the target.
    skip : Callable[[], bool], default: lambda: False
        Callable returning `True` when this step should be skipped.
    ensure_visible : Callable[[], bool], default: lambda: False
        Callable run before showing the step. Return `True` if it just
        revealed or relaid out the target so geometry should be read on the
        next event-loop tick.
    """

    target: Callable[[], QWidget | None]
    title: str
    body: str
    anchor: TourAnchor = TourAnchor.RIGHT
    skip: Callable[[], bool] = lambda: False
    # Return True when this just revealed/layout-changed the target. The tour
    # waits one event-loop tick before reading geometry.
    ensure_visible: Callable[[], bool] = lambda: False


_TOOLTIP_WIDTH = 340


class _TourTooltip(QFrame):
    """Popover widget that displays a tour step and navigation buttons.

    Parameters
    ----------
    parent : QWidget
        Parent widget that owns the tooltip.
    """

    next_clicked = Signal()
    back_clicked = Signal()
    skip_clicked = Signal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("qt_tour_tooltip")
        self.setStyleSheet(
            "#qt_tour_tooltip { "
            "background-color: palette(window); "
            "color: palette(window-text); "
            "border: 1px solid palette(mid); "
            "border-radius: 6px; "
            "padding: 0; "
            "}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        self._title = QLabel()
        self._title.setObjectName("qt_tour_title")
        self._title.setWordWrap(True)
        title_font = QFont(self.font())
        title_font.setBold(True)
        self._title.setFont(title_font)
        layout.addWidget(self._title)

        self._body = QLabel()
        self._body.setObjectName("qt_tour_body")
        self._body.setWordWrap(True)
        self._body.setOpenExternalLinks(True)
        layout.addWidget(self._body)

        self._nav = QHBoxLayout()
        self._nav.setSpacing(8)
        self._counter = QLabel()
        self._counter.setObjectName("qt_tour_counter")
        self._nav.addWidget(self._counter)
        self._nav.addStretch()
        self._back = QPushButton()
        self._back.setObjectName("qt_tour_back")
        self._back.clicked.connect(self.back_clicked)
        self._nav.addWidget(self._back)
        self._next = QPushButton()
        self._next.setObjectName("qt_tour_next")
        self._next.clicked.connect(self.next_clicked)
        self._nav.addWidget(self._next)
        self._skip = QPushButton()
        self._skip.setObjectName("qt_tour_skip")
        self._skip.clicked.connect(self.skip_clicked)
        self._nav.addWidget(self._skip)
        layout.addLayout(self._nav)

    def _update_size(self) -> None:
        """Resize the tooltip to fit content and navigation labels."""
        layout = self.layout()
        if layout is None:
            return
        self._nav.invalidate()
        margins = layout.contentsMargins()
        nav_width = self._nav.sizeHint().width() + margins.left() + margins.right()
        width = max(_TOOLTIP_WIDTH, nav_width)
        self.setFixedWidth(width)
        self.setFixedHeight(layout.heightForWidth(width))
        layout.activate()

    def set_content(self, title: str, body: str, step: int, total: int) -> None:
        """Set the displayed step content.

        Parameters
        ----------
        title : str
            Step title.
        body : str
            Step body text.
        step : int
            One-based visible step number.
        total : int
            Total visible step count.
        """
        self._title.setText(title)
        self._body.setText(body)
        self._counter.setText(f"{step}/{total}")
        self._back.setText("Previous")
        self._skip.setText("(Esc) Skip")
        self._next.setText("Finish" if step == total else "Next")
        self._back.setVisible(step > 1)
        self._skip.setVisible(step < total)
        self._update_size()

    def place(self, target_rect: QRect, anchor: TourAnchor, bounds: QRect) -> None:
        """Place the tooltip relative to a target rectangle.

        Parameters
        ----------
        target_rect : QRect
            Target geometry in parent-window coordinates.
        anchor : TourAnchor
            Preferred tooltip placement.
        bounds : QRect
            Rectangle the tooltip must stay inside.
        """
        gap = 12
        w, h = self.width(), self.height()
        if anchor == TourAnchor.LEFT:
            x, y = target_rect.left() - w - gap, target_rect.top()
        elif anchor == TourAnchor.ABOVE:
            x, y = target_rect.center().x() - w // 2, target_rect.top() - h - gap
        elif anchor == TourAnchor.BELOW:
            x, y = target_rect.center().x() - w // 2, target_rect.bottom() + gap
        elif anchor == TourAnchor.CENTER:
            x, y = (
                target_rect.center().x() - w // 2,
                target_rect.center().y() - h // 2,
            )
        else:
            x, y = target_rect.right() + gap, target_rect.top()
        x = max(bounds.left() + 8, min(x, bounds.right() - w - 8))
        y = max(bounds.top() + 8, min(y, bounds.bottom() - h - 8))
        self.move(x, y)


class _TourOverlay(QWidget):
    """Translucent overlay with an optional spotlight cutout.

    Parameters
    ----------
    parent : QWidget
        Parent widget covered by the overlay.
    """

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._spotlight: QRect | None = None

    def set_spotlight(self, rect: QRect | None) -> None:
        """Set the target rectangle left uncovered by the overlay.

        Parameters
        ----------
        rect : QRect or None
            Spotlight rectangle in overlay coordinates. If `None`, cover the
            whole parent.
        """
        self._spotlight = rect
        self.update()

    def paintEvent(self, a0: QPaintEvent | None) -> None:
        """Paint the dimmed overlay.

        Parameters
        ----------
        a0 : QPaintEvent or None
            Qt paint event.
        """
        del a0
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        overlay = QColor(0, 0, 0, 150)
        if self._spotlight is None:
            painter.fillRect(self.rect(), overlay)
            return

        rect = self._spotlight.adjusted(-6, -6, 6, 6)
        painter.fillRect(0, 0, self.width(), rect.top(), overlay)
        painter.fillRect(
            0,
            rect.bottom() + 1,
            self.width(),
            self.height() - rect.bottom() - 1,
            overlay,
        )
        painter.fillRect(0, rect.top(), rect.left(), rect.height(), overlay)
        painter.fillRect(
            rect.right() + 1,
            rect.top(),
            self.width() - rect.right() - 1,
            rect.height(),
            overlay,
        )


class GuidedTour(QObject):
    """Run a guided tour over a sequence of `TourStep` objects.

    Parameters
    ----------
    steps : Sequence[TourStep]
        Ordered tour steps.
    parent_window : QWidget
        Window or top-level widget the overlay and tooltip are parented to.
    """

    finished = Signal()

    def __init__(self, steps: Sequence[TourStep], parent_window: QWidget) -> None:
        """Create a guided tour.

        Parameters
        ----------
        steps : Sequence[TourStep]
            Ordered tour steps.
        parent_window : QWidget
            Window or top-level widget the overlay and tooltip are parented to.
        """
        if not isinstance(parent_window, QWidget):
            raise TypeError("parent_window must be a QWidget")
        super().__init__(parent_window)
        self._steps = list(steps)
        self._window: QWidget | None = parent_window
        self._current = 0
        self._active = False
        self._overlay = _TourOverlay(parent_window)
        self._tooltip = _TourTooltip(parent_window)
        self._tooltip.next_clicked.connect(self._on_next)
        self._tooltip.back_clicked.connect(self._on_back)
        self._tooltip.skip_clicked.connect(self.close)

    def start(self) -> None:
        """Start the tour."""
        if self._active or self._window is None:
            return
        self._active = True
        self._overlay.setGeometry(self._window.rect())
        self._overlay.show()
        self._overlay.raise_()
        self._tooltip.show()
        self._tooltip.raise_()
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)
        start_index = self._seek(0, 1)
        if start_index is None:
            self.close()
            return
        QTimer.singleShot(0, lambda: self._show_step(start_index))

    def close(self) -> None:  # type: ignore[override]
        """Close the tour and emit `finished`."""
        if not self._active or self._window is None:
            return
        self._active = False
        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self)
        self._tooltip.next_clicked.disconnect(self._on_next)
        self._tooltip.back_clicked.disconnect(self._on_back)
        self._tooltip.skip_clicked.disconnect(self.close)
        self._overlay.hide()
        self._tooltip.hide()
        self._overlay.setParent(None)
        self._tooltip.setParent(None)
        self._overlay.deleteLater()
        self._tooltip.deleteLater()
        self.finished.emit()
        self.setParent(None)
        self._window = None
        self.deleteLater()

    close_tour = close

    def eventFilter(self, a0: QObject | None, a1: QEvent | None) -> bool:
        """Handle resize and Escape events while the tour is active.

        Parameters
        ----------
        a0 : QObject or None
            Watched object.
        a1 : QEvent or None
            Event sent to the watched object.

        Returns
        -------
        bool
            `True` if the event was handled by the tour.
        """
        if a1 is None:
            return super().eventFilter(a0, a1)
        if a0 is self._window and a1.type() == QEvent.Type.Resize:
            self._show_step(self._current)
        elif a1.type() == QEvent.Type.KeyPress:
            if isinstance(a1, QKeyEvent) and a1.key() == Qt.Key.Key_Escape:
                self.close()
                return True
        return super().eventFilter(a0, a1)

    @staticmethod
    def _is_available(step: TourStep) -> bool:
        """Return whether a step can currently be shown.

        Parameters
        ----------
        step : TourStep
            Step to check.

        Returns
        -------
        bool
            `True` when the step is not skipped and resolves to a widget.
        """
        return not step.skip() and step.target() is not None

    def _seek(self, index: int, direction: int) -> int | None:
        """Find the next available step index.

        Parameters
        ----------
        index : int
            Starting index.
        direction : int
            Direction to search, usually `1` or `-1`.

        Returns
        -------
        int or None
            Matching step index, or `None` if no step is available.
        """
        while 0 <= index < len(self._steps):
            if self._is_available(self._steps[index]):
                return index
            index += direction
        return None

    def _on_next(self) -> None:
        """Advance to the next available step or finish the tour."""
        next_index = self._seek(self._current + 1, 1)
        if next_index is None:
            self.close()
            return
        self._show_step(next_index)

    def _on_back(self) -> None:
        """Return to the previous available step."""
        prev_index = self._seek(self._current - 1, -1)
        if prev_index is not None:
            self._show_step(prev_index)

    def _show_step(self, index: int) -> None:
        """Show a step by index.

        Parameters
        ----------
        index : int
            Step index in `self._steps`.
        """
        if self._window is None:
            return
        step = self._steps[index]
        if step.ensure_visible():
            QTimer.singleShot(0, lambda: self._show_step(index))
            return
        target = step.target()
        if target is None or not target.isVisible():
            return
        self._current = index
        visible = [i for i, s in enumerate(self._steps) if self._is_available(s)]
        top_left = target.mapTo(self._window, QPoint(0, 0))
        rect = QRect(top_left, target.size())
        self._overlay.setGeometry(self._window.rect())
        self._overlay.set_spotlight(rect)
        self._tooltip.set_content(
            step.title,
            step.body,
            visible.index(index) + 1,
            len(visible),
        )
        self._tooltip.place(rect, step.anchor, self._window.rect())
        self._tooltip.raise_()
