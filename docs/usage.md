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

The tooltip is a normal Qt widget. Style it with your application stylesheet.
If you style `#qt_tour_tooltip`, provide the full box style; partial QSS like
only `border-radius` can disable native background painting in Qt.

```python
app.setStyleSheet("""
#qt_tour_tooltip {
    background: palette(window);
    color: palette(window-text);
    border: 1px solid palette(mid);
    border-radius: 8px;
}
#qt_tour_title {
    font-weight: 700;
}
""")
```
