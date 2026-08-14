from __future__ import annotations

import sys

from qtpy.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from qt_tour import GuidedTour, TourAnchor, TourStep


class Window(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("qt-tour example")
        self.resize(760, 460)

        self.toolbar = QToolBar("Tools")
        self.addToolBar(self.toolbar)
        self.tour_button = QPushButton("Take a tour")
        self.toolbar.addWidget(self.tour_button)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        form = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Dataset path")
        self.run_button = QPushButton("Run")
        form.addWidget(QLabel("Input:"))
        form.addWidget(self.input)
        form.addWidget(self.run_button)
        layout.addLayout(form)

        self.results = QTextEdit()
        self.results.setPlaceholderText("Results appear here")
        layout.addWidget(self.results)

        self.status = self.statusBar()
        assert self.status is not None
        self.status.showMessage("Ready")

        self._tour: GuidedTour | None = None
        self.tour_button.clicked.connect(self.start_tour)

    def start_tour(self) -> None:
        self._tour = GuidedTour(
            [
                TourStep(
                    lambda: self.tour_button,
                    "Take the tour",
                    "Restart this tour from here any time.",
                    TourAnchor.BELOW,
                ),
                TourStep(
                    lambda: self.input,
                    "Choose input",
                    "Enter or paste the data you want to process.",
                ),
                TourStep(
                    lambda: self.run_button,
                    "Run analysis",
                    "Click Run when your input is ready.",
                    TourAnchor.LEFT,
                ),
                TourStep(
                    lambda: self.results,
                    "Read results",
                    "Output and logs appear here.",
                    TourAnchor.ABOVE,
                ),
                TourStep(
                    lambda: self.status,
                    "Status",
                    "Short progress messages appear in the status bar.",
                    TourAnchor.ABOVE,
                ),
            ],
            self,
        )
        self._tour.finished.connect(lambda: setattr(self, "_tour", None))
        self._tour.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
