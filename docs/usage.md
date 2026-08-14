# Usage

## Public API

```python
from qt_tour import GuidedTour, TourAnchor, TourStep
```

## Step fields

```python
TourStep(
    target=lambda: widget,
    title="Title",
    body="Body text",
    anchor=TourAnchor.RIGHT,
    skip=lambda: False,
    ensure_visible=lambda: False,
)
```

- `target`: callable returning a `QWidget | None`. `None` skips the step.
- `title`: popover title.
- `body`: popover body. Qt rich text links work.
- `anchor`: `LEFT`, `RIGHT`, `ABOVE`, `BELOW`, or `CENTER`.
- `skip`: return `True` to skip a step conditionally.
- `ensure_visible`: show/reveal the target if needed. Return `True` when layout
  may need one event-loop tick before geometry is read.

## Completion

```python
tour = GuidedTour([...], window)
tour.finished.connect(clean_up)
tour.start()
```

Escape or Skip closes the tour.

## Styling

The tooltip is a normal Qt widget. Style it with your application stylesheet:

```python
app.setStyleSheet("""
#qt_tour_tooltip {
    background: #2b2b2b;
    color: white;
    border: 1px solid #555;
    border-radius: 8px;
}
#qt_tour_title {
    font-size: 16px;
    font-weight: bold;
}
#qt_tour_body {
    color: #ddd;
}
#qt_tour_counter {
    color: #aaa;
}
#qt_tour_tooltip QPushButton {
    padding: 4px 10px;
}
""")
```
