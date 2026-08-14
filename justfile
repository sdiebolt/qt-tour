# Show available recipes.
default:
    just --list

# Show available recipes.
help:
    just --list

# Run pre-commit hooks on all files.
precommit:
    uv run prek run --all-files

# Run tests headlessly.
test:
    QT_QPA_PLATFORM=offscreen uv run pytest

# Capture the README/docs demo GIFs from the example app.
demo:
    QT_QPA_PLATFORM=offscreen uv run python scripts/screenshot.py

# Build documentation into site/.
docs:
    uv run zensical build

# Serve documentation locally.
docs-serve:
    uv run zensical serve

# Build sdist and wheel.
build:
    uv build

# Run the example app.
example:
    uv run python examples/basic.py

# Run the usual local checks.
check: precommit test
