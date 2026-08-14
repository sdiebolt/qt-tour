from __future__ import annotations

from qtpy.QtCore import QRect, Qt
from qtpy.QtWidgets import QApplication, QWidget

from qt_tour import GuidedTour, TourAnchor, TourStep
from qt_tour._tour import _TOOLTIP_WIDTH, _TourTooltip


def _window(qtbot) -> QWidget:
    window = QWidget()
    qtbot.addWidget(window)
    window.resize(640, 480)
    window.show()
    return window


def _child(parent: QWidget, rect: QRect) -> QWidget:
    widget = QWidget(parent)
    widget.setGeometry(rect)
    widget.show()
    return widget


def _wait_title(qtbot, tour: GuidedTour, title: str) -> None:
    qtbot.waitUntil(lambda: tour._steps[tour._current].title == title)


def test_start_next_back_finish(qtbot):
    window = _window(qtbot)
    first = _child(window, QRect(0, 0, 50, 50))
    second = _child(window, QRect(60, 0, 50, 50))
    tour = GuidedTour(
        [
            TourStep(lambda: first, "First", "one"),
            TourStep(lambda: second, "Second", "two"),
        ],
        window,
    )

    with qtbot.waitSignal(tour.finished, timeout=1000):
        tour.start()
        _wait_title(qtbot, tour, "First")
        qtbot.mouseClick(tour._tooltip._next, Qt.MouseButton.LeftButton)
        _wait_title(qtbot, tour, "Second")
        qtbot.mouseClick(tour._tooltip._back, Qt.MouseButton.LeftButton)
        _wait_title(qtbot, tour, "First")
        qtbot.mouseClick(tour._tooltip._next, Qt.MouseButton.LeftButton)
        _wait_title(qtbot, tour, "Second")
        qtbot.mouseClick(tour._tooltip._next, Qt.MouseButton.LeftButton)


def test_escape_closes_regardless_of_focus(qtbot):
    window = _window(qtbot)
    target = _child(window, QRect(0, 0, 50, 50))
    target.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    tour = GuidedTour([TourStep(lambda: target, "Only", "")], window)
    tour.start()
    _wait_title(qtbot, tour, "Only")

    target.setFocus()
    qtbot.waitUntil(lambda: QApplication.focusWidget() is target)
    with qtbot.waitSignal(tour.finished, timeout=1000):
        qtbot.keyPress(target, Qt.Key.Key_Escape)


def test_skip_button_closes(qtbot):
    window = _window(qtbot)
    target = _child(window, QRect(0, 0, 50, 50))
    tour = GuidedTour([TourStep(lambda: target, "Only", "")], window)
    tour.start()
    _wait_title(qtbot, tour, "Only")

    with qtbot.waitSignal(tour.finished, timeout=1000):
        qtbot.mouseClick(tour._tooltip._skip, Qt.MouseButton.LeftButton)


def test_skips_missing_and_conditional_steps(qtbot):
    window = _window(qtbot)
    first = _child(window, QRect(0, 0, 50, 50))
    last = _child(window, QRect(60, 0, 50, 50))
    tour = GuidedTour(
        [
            TourStep(lambda: first, "First", ""),
            TourStep(lambda: None, "Missing", ""),
            TourStep(lambda: first, "Skipped", "", skip=lambda: True),
            TourStep(lambda: last, "Last", ""),
        ],
        window,
    )
    tour.start()
    _wait_title(qtbot, tour, "First")

    qtbot.mouseClick(tour._tooltip._next, Qt.MouseButton.LeftButton)
    _wait_title(qtbot, tour, "Last")
    assert tour._tooltip._counter.text() == "2/2"
    tour.close()


def test_all_steps_unavailable_finishes(qtbot):
    window = _window(qtbot)
    tour = GuidedTour([TourStep(lambda: None, "Missing", "")], window)
    with qtbot.waitSignal(tour.finished, timeout=1000):
        tour.start()


def test_hidden_widget_can_be_revealed(qtbot):
    window = _window(qtbot)
    hidden = QWidget(window)
    hidden.setGeometry(0, 0, 50, 50)
    shown: list[QWidget] = []

    def reveal() -> bool:
        if hidden.isVisible():
            return False
        shown.append(hidden)
        hidden.show()
        return True

    tour = GuidedTour(
        [
            TourStep(lambda: window, "Welcome", ""),
            TourStep(lambda: hidden, "Hidden", "", ensure_visible=reveal),
        ],
        window,
    )
    tour.finished.connect(lambda: [w.hide() for w in shown])
    tour.start()
    _wait_title(qtbot, tour, "Welcome")

    qtbot.mouseClick(tour._tooltip._next, Qt.MouseButton.LeftButton)
    _wait_title(qtbot, tour, "Hidden")
    assert hidden.isVisible()
    tour.close()
    assert not hidden.isVisible()


def test_hidden_target_without_reveal_does_not_advance(qtbot):
    window = _window(qtbot)
    first = _child(window, QRect(0, 0, 50, 50))
    hidden = QWidget(window)
    hidden.setGeometry(60, 0, 50, 50)
    tour = GuidedTour(
        [TourStep(lambda: first, "First", ""), TourStep(lambda: hidden, "Hidden", "")],
        window,
    )
    tour.start()
    _wait_title(qtbot, tour, "First")
    qtbot.mouseClick(tour._tooltip._next, Qt.MouseButton.LeftButton)
    assert tour._steps[tour._current].title == "First"
    tour.close()


def test_target_positioning_and_resize(qtbot):
    window = _window(qtbot)
    target = _child(window, QRect(100, 120, 80, 40))
    tour = GuidedTour([TourStep(lambda: target, "Target", "")], window)
    tour.start()
    qtbot.waitUntil(lambda: tour._overlay._spotlight is not None)

    assert tour._overlay.geometry() == window.rect()
    assert tour._overlay._spotlight == QRect(100, 120, 80, 40)
    before = tour._tooltip.pos()
    window.resize(800, 600)
    qtbot.waitUntil(lambda: tour._overlay.geometry() == window.rect())
    assert tour._tooltip.pos() == before
    tour.close()


def test_each_anchor_direction_places_tooltip(qtbot):
    parent = QWidget()
    qtbot.addWidget(parent)
    parent.resize(1200, 900)
    tooltip = _TourTooltip(parent)
    qtbot.addWidget(tooltip)
    tooltip.set_content("Title", "Body", 2, 5)
    target = QRect(500, 400, 100, 80)
    bounds = QRect(0, 0, 1200, 900)

    tooltip.place(target, TourAnchor.LEFT, bounds)
    assert tooltip.geometry().right() < target.left()
    tooltip.place(target, TourAnchor.RIGHT, bounds)
    assert tooltip.geometry().left() > target.right()
    tooltip.place(target, TourAnchor.ABOVE, bounds)
    assert tooltip.geometry().bottom() < target.top()
    tooltip.place(target, TourAnchor.BELOW, bounds)
    assert tooltip.geometry().top() > target.bottom()
    tooltip.place(target, TourAnchor.CENTER, bounds)
    assert abs(tooltip.geometry().center().x() - target.center().x()) <= 1
    assert abs(tooltip.geometry().center().y() - target.center().y()) <= 1


def test_tooltip_widens_for_long_nav_labels(qtbot):
    parent = QWidget()
    qtbot.addWidget(parent)
    tooltip = _TourTooltip(parent)
    qtbot.addWidget(tooltip)
    tooltip.set_content("Title", "Body", 2, 5)
    assert tooltip.width() == _TOOLTIP_WIDTH

    tooltip._back.setText("Previous step in the guided tour")
    tooltip._next.setText("Next step in the guided tour")
    tooltip._skip.setText("Skip this entire guided tour now")
    tooltip._update_size()
    assert tooltip.width() > _TOOLTIP_WIDTH


def test_cleanup_disconnects_and_removes_event_filter(qtbot):
    window = _window(qtbot)
    target = _child(window, QRect(0, 0, 50, 50))
    tour = GuidedTour([TourStep(lambda: target, "Only", "")], window)
    tour.start()
    _wait_title(qtbot, tour, "Only")
    tooltip = tour._tooltip

    tour.close()
    assert tour._window is None
    assert not tour._active
    # Button click after close must not emit through disconnected tour slots.
    qtbot.mouseClick(tooltip._next, Qt.MouseButton.LeftButton)
