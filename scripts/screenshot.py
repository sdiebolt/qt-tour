from __future__ import annotations

import sys
from pathlib import Path

from qtpy.QtCore import Qt, QTimer
from qtpy.QtGui import QColor, QPalette
from qtpy.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from examples.basic import Window


def _set_dark_palette(app: QApplication) -> None:
    """Apply a small dark Qt palette for screenshots.

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
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(90, 160, 255))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(90, 160, 255))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    app.setPalette(palette)


def _grab(name: str, dark: bool) -> None:
    """Grab one themed example screenshot.

    Parameters
    ----------
    name : str
        Output file stem.
    dark : bool
        Whether to apply the dark palette.
    """
    existing_app = QApplication.instance()
    app = (
        existing_app
        if isinstance(existing_app, QApplication)
        else QApplication(sys.argv)
    )
    app.setStyle("Fusion")
    if dark:
        _set_dark_palette(app)

    window = Window()
    window.show()
    window.start_tour()

    out = Path(f"docs/images/{name}.png")
    out.parent.mkdir(parents=True, exist_ok=True)

    def grab() -> None:
        window.grab().save(str(out))
        window.close()
        app.quit()

    QTimer.singleShot(300, grab)
    app.exec()


def main() -> int:
    """Capture light and dark example screenshots.

    Returns
    -------
    int
        Process exit code.
    """
    _grab("screenshot-light", dark=False)
    _grab("screenshot-dark", dark=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
