# syntax=docker/dockerfile:1

# Pinned uv release + Trixie-based Python image (Astral moved off Bookworm
# defaults as of uv 0.9 — see backend/Dockerfile for the same note).
FROM ghcr.io/astral-sh/uv:0.11-python3.12-trixie-slim

WORKDIR /app

# Same layer-caching reasoning as the backend Dockerfile: dependency
# manifests first, so code changes don't invalidate the dependency layer.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen

COPY app.py api_client.py ./

EXPOSE 8501

# API_BASE_URL is intentionally NOT baked in here — it's supplied at
# `docker run` / compose time via environment variables, so the same image
# works against a local backend or a deployed one without a rebuild.

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD uv run python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=3)" || exit 1

CMD ["uv", "run", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]