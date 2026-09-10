# syntax=docker/dockerfile:1

# Official uv base image — ships uv itself, no separate pip-install-uv step needed.
# Pinned to a specific uv release line (not just ":python3.12-trixie-slim") so a
# rebuild next month doesn't silently pick up a newer uv version.
# Note: Astral's python-tagged images moved from Debian Bookworm to Trixie
# defaults as of uv 0.9 — "python3.12-bookworm-slim" is no longer published.
FROM ghcr.io/astral-sh/uv:0.11-python3.12-trixie-slim

WORKDIR /app

# Copy only the dependency manifests first so this layer is cached as long as
# dependencies don't change, even when application code does. This is the
# main reason to split this into two COPY steps instead of one.
COPY pyproject.toml uv.lock README.md ./

# --frozen: install exactly what's in uv.lock, never re-resolve. This is what
# makes the container's dependency set reproducible instead of "whatever
# versions happened to be current when the image was built."
# --no-dev: pytest/httpx aren't needed to run the API in production.
RUN uv sync --frozen --no-dev

# Now copy the rest of the application code.
COPY app ./app

# NOTE: the persisted vector store (data/vector_store/) and the project
# registry (data/projects.json) are intentionally NOT copied into the image.
# They're runtime state, produced by the notebook (vector store) and by the
# app itself (registry) — mount them as a volume at `docker run` time so
# they survive container restarts and rebuilds. See README for the exact
# `docker run -v` / docker-compose volume mapping.

EXPOSE 8000

# Basic container-level health check, hitting the same /health the plan requires.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD uv run python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)" || exit 1

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]