# qt-tour

Small guided tours for Python Qt applications.

![qt-tour light demo](images/demo-light.gif#only-light)
![qt-tour dark demo](images/demo-dark.gif#only-dark)

Use it when you want to highlight ordinary `QWidget`s and show a short
step-by-step popover next to them.

```python
from qt_tour import GuidedTour, TourAnchor, TourStep

GuidedTour(
    [
        TourStep(lambda: button, "Load data", "Load your dataset here."),
        TourStep(
            lambda: results,
            "Results",
            "Results will appear here.",
            anchor=TourAnchor.ABOVE,
        ),
    ],
    window,
).start()
```

## Install

```bash
uv add qt-tour
uv add PyQt6  # or PySide6
```

Runtime dependency: `qtpy`.

Qt binding: bring your own PyQt/PySide.
