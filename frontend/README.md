# SpecWise Frontend

Streamlit chat UI for SpecWise. See the [root README](../README.md) for the whole-system overview, and [`SETUP_AND_VERIFICATION_GUIDE.md`](../SETUP_AND_VERIFICATION_GUIDE.md) for a full setup walkthrough with a UI verification checklist.

## Quick Start

```bash
cd frontend
cp .env.example .env
uv sync --frozen
uv run streamlit run app.py
```

Requires the backend running and reachable at `API_BASE_URL` (default `http://localhost:8000`).

Opens at `http://localhost:8501`.

## What It Does

- **Sidebar** — project selector, project creation form, document upload (for the active project)
- **Chat tab** — ask questions, see the generated answer with an expandable "Sources" list citing `doc_name`/`section`
- **Search tab** — semantic search against the active project's documents, returning ranked chunks with distances instead of a generated answer

## Module Overview

**`api_client.py`** — every backend call goes through here, never through `requests` directly from `app.py`. Every function returns the same shape:

```python
{"ok": bool, "data": ..., "error": str | None}
```

This means `app.py` never wraps a call in its own try/except — every call site is just:

```python
result = api_client.query(question, project_id)
if result["ok"]:
    ...
else:
    st.error(result["error"])
```

Connection errors, timeouts, and HTTP error responses are all normalized into this same shape inside `_request()`/`_handle_response()`.

**`app.py`** — the UI itself. Streamlit reruns the entire script on every interaction, so anything that needs to persist across reruns lives in `st.session_state`:

- `project_id` — the currently active project
- `chat_history` — list of `{question, answer, sources}` dicts, so previous exchanges stay visible as you keep chatting

## Environment Variables

| Variable         | Default                   | Purpose                                                                                                                                                    |
| ---------------- | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `API_BASE_URL` | `http://localhost:8000` | Backend URL. Read via`python-dotenv` in `api_client.py` — never hard-coded in either file. Change this (not the code) to point at a deployed backend. |

## Testing

There's no committed automated test suite for the frontend yet — verification is currently manual, via the checklist in `SETUP_AND_VERIFICATION_GUIDE.md` Step 4 (create a project, upload a doc, ask a grounded question, ask an unanswerable one, check the Search tab, confirm two projects stay isolated visually).

If you want an automated suite later, Streamlit ships a headless testing framework (`streamlit.testing.v1.AppTest`) that can drive `app.py` and assert on rendered output without a browser — worth adding if the UI grows past what's comfortable to manually re-check every time.
