from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image
from qtpy.QtCore import Qt, QTimer
from qtpy.QtGui import QColor, QImage, QPalette, QPixmap
from qtpy.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from examples.basic import Window


def _set_dark_palette(app: QApplication) -> None:
    """Apply a small dark Qt palette for demos.

    Parameters
    ----------
    app : QApplication
        Application to style.
    """
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(43, 43, 43))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(43, 43, 43))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(43, 43, 43))
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(180, 180, 180))
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(90, 160, 255))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(90, 160, 255))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    app.setPalette(palette)
    app.setStyleSheet(
        "#qt_tour_tooltip { "
        "background: palette(window); "
        "color: palette(window-text); "
        "border: 1px solid palette(mid); "
        "border-radius: 8px; "
        "}"
        "#qt_tour_title { font-weight: 700; }"
        "QLineEdit, QTextEdit { "
        "background: #1e1e1e; color: white; border: 1px solid #555; "
        "selection-background-color: #5aa0ff; selection-color: black; "
        "}"
    )


def _app() -> QApplication:
    """Return a QApplication instance.

    Returns
    -------
    QApplication
        Existing or newly-created application.
    """
    existing_app = QApplication.instance()
    return (
        existing_app
        if isinstance(existing_app, QApplication)
        else QApplication(sys.argv)
    )


def _pixmap_to_image(pixmap: QPixmap) -> Image.Image:
    """Convert a Qt pixmap to a Pillow image.

    Parameters
    ----------
    pixmap : QPixmap
        Pixmap to convert.

    Returns
    -------
    PIL.Image.Image
        RGB image.
    """
    image = pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
    width = image.width()
    height = image.height()
    data = image.bits().asstring(width * height * 4)
    return Image.frombytes("RGBA", (width, height), data).convert("RGB")


def _reset_style(app: QApplication) -> None:
    """Reset app styling before capturing a new theme.

    Parameters
    ----------
    app : QApplication
        Application to reset.
    """
    style = app.style()
    if style is not None:
        app.setPalette(style.standardPalette())
    app.setStyleSheet("")


def _grab_demo(name: str, dark: bool) -> None:
    """Capture a short tour walkthrough GIF.

    Parameters
    ----------
    name : str
        Output file stem.
    dark : bool
        Whether to apply the dark palette.
    """
    app = _app()
    app.setStyle("Fusion")
    _reset_style(app)
    if dark:
        _set_dark_palette(app)

    window = Window()
    window.show()
    window.start_tour()

    out = Path(f"docs/images/{name}.gif")
    out.parent.mkdir(parents=True, exist_ok=True)
    frames: list[Image.Image] = []

    def capture_and_advance() -> None:
        frames.append(_pixmap_to_image(window.grab()))
        tour = window._tour
        if tour is None or tour._tooltip._next.text() == "Finish":
            frames.append(_pixmap_to_image(window.grab()))
            frames[0].save(
                out,
                save_all=True,
                append_images=frames[1:],
                duration=900,
                loop=0,
                optimize=True,
            )
            window.close()
            app.quit()
            return
        tour._tooltip._next.click()
        QTimer.singleShot(350, capture_and_advance)

    QTimer.singleShot(350, capture_and_advance)
    app.exec()


def main() -> int:
    """Capture documentation demo GIFs.

    Returns
    -------
    int
        Process exit code.
    """
    _grab_demo("demo-light", dark=False)
    _grab_demo("demo-dark", dark=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
