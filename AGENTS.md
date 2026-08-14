# AGENTS.md

## Project

`qt-tour` is a small Python package for guided tours in Python Qt apps.
Runtime stays minimal: `qtpy` only. Users provide a Qt binding (`PyQt6`,
`PySide6`, etc.).

## Public API

Keep public API tiny:

```python
from qt_tour import GuidedTour, TourStep, TourAnchor
```

Core targets are ordinary `QWidget`s. Do not add app-specific target registries,
YAML formats, persistence, analytics, plugin systems, or theme frameworks unless
explicitly requested.

## Development

Use `uv`.

Useful commands:

```bash
just help
just check        # prek + tests
just precommit    # ruff, ty, docs build hooks
just test         # headless pytest
just docs         # zensical build
just docs-serve   # local docs server
just demo         # regenerate docs/images/demo-*.gif
just build        # uv build
```

If `just` is unavailable, run the underlying commands from `justfile`.

## Checks

Before committing meaningful changes, run:

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run zensical build
QT_QPA_PLATFORM=offscreen uv run pytest
```

GUI tests run headlessly with `QT_QPA_PLATFORM=offscreen`.

## Styling rule

The library should not impose heavy QSS. Default widgets should use Qt palette
and native styling. QSS customization is exposed through object names:

- `#qt_tour_tooltip`
- `#qt_tour_title`
- `#qt_tour_body`
- `#qt_tour_counter`
- `#qt_tour_back`
- `#qt_tour_next`
- `#qt_tour_skip`

If styling `#qt_tour_tooltip`, include full box styling (`background`, `color`,
`border`, etc.); partial QSS like only `border-radius` can disable native Qt
background painting.

## Docs and demos

Docs use Zensical (`zensical.toml`, `docs/`). API docs use mkdocstrings.
Regenerate GIFs after visual/example changes:

```bash
QT_QPA_PLATFORM=offscreen uv run python scripts/screenshot.py
```

README uses the dark demo GIF. Docs home switches light/dark GIFs using
`#only-light` / `#only-dark` fragments.

## Commits and releases

Use Commitizen-style commit subjects, e.g.:

```text
feat: add ...
fix: handle ...
docs: update ...
style: format ...
chore: release ...
```

Release flow:

1. bump `version` in `pyproject.toml`
2. `uv lock`
3. run checks/build
4. commit `chore: release X.Y.Z`
5. tag `vX.Y.Z`
6. publish GitHub release

PyPI publishing uses GitHub Trusted Publishing via `.github/workflows/release.yml`.
