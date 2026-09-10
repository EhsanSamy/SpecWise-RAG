# SpecWise Backend

FastAPI service implementing the project-aware RAG API: retrieval, generation with grounded refusal, project management, document ingestion, and semantic search. See the [root README](../README.md) for the whole-system overview and architecture diagram, and [`SETUP_AND_VERIFICATION_GUIDE.md`](../SETUP_AND_VERIFICATION_GUIDE.md) for a full step-by-step setup walkthrough.

## Quick Start

```bash
cd backend
cp .env.example .env
uv sync --frozen
uv run uvicorn app.main:app --reload
```

Requires `backend/data/vector_store/` to already exist — built by running `notebooks/rag_pipeline.ipynb` first. Without it, `/health` will report `retrieval_ready: false` and `/query`/`/search` will 404 on the default collection.

Swagger UI: `http://localhost:8000/docs`

## Module Overview

```
app/
├── main.py                 # App entrypoint. Lifespan startup loads the vector
│                              store + embedding model ONCE — never per-request.
├── core/config.py          # Env-driven Settings (pydantic-settings), cached via
│                              @lru_cache. Every other module reads config from here.
├── schemas/                 # Pydantic request/response contracts, one file per resource
├── services/
│   ├── retrieval.py         # Owns the Chroma client + embedding model as module-level
│   │                          singletons. retrieve() never mixes collections across
│   │                          projects — resolved once per call via project_id.
│   ├── generation.py        # Grounded-refusal gate (distance threshold), prompt
│   │                          template, Ollama call. Never imported by search.py.
│   ├── ingestion.py         # parse → clean → chunk → embed → store, for uploads.
│   │                          Reuses retrieval.py's already-loaded model/client.
│   └── project_store.py     # Persisted JSON registry for project metadata
│                              (id, name, created_at, document_count).
├── api/routes/               # Thin route handlers — validate via schema, call
│                              services, shape the response. No business logic here.
└── utils/logging_config.py  # Central logging setup, called once at startup.
```

## Endpoints

### `GET /health`

```bash
curl http://localhost:8000/health
```

`{"status": "ok", "retrieval_ready": true}`

### `POST /query`

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Can a member reserve a book that is already checked out?", "project_id": null}'
```

`project_id` is optional — omit it to use `DEFAULT_PROJECT_ID`. Returns `{answer, sources, refused}`. If the top retrieved chunk's distance exceeds `DISTANCE_THRESHOLD`, the LLM is never called and `refused: true` comes back instead.

### `POST /projects`

```bash
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "E-Commerce Platform v2", "description": "optional"}'
```

Creates the project's metadata entry **and** its empty Chroma collection in the same call — a document upload or query against the returned `id` works immediately.

### `GET /projects`

```bash
curl http://localhost:8000/projects
```

### `POST /projects/{project_id}/documents`

```bash
curl -X POST http://localhost:8000/projects/<project_id>/documents \
  -F "file=@./data/sample_project/SRS.md"
```

Supports `.md`, `.txt`, `.pdf`. A parsing failure (e.g. a scanned PDF with no text layer) comes back as `{"status": "failed", "error": "..."}`, not a 500 — `document_count` is only incremented on success.

### `POST /search`

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"question": "reservation rules", "project_id": "<project_id>"}'
```

Same retrieval as `/query`, no generation, no refusal gate — returns ranked chunks directly with their distance, so a weak match still comes back as a result rather than being hidden.

## Environment Variables

See `.env.example` for the full, current list with defaults. The two most likely to need changing:

| Variable               | Why you'd change it                                                                                               |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `DISTANCE_THRESHOLD` | Tune this against real questions on your real documents — see the notebook's Phase 3 manual-test section for how |
| `OLLAMA_HOST`        | Defaults to`http://localhost:11434`; set to `http://ollama:11434` under `docker-compose`                    |

## Testing

```bash
uv run pytest -v
```

14 tests across `test_query.py`, `test_projects.py`, `test_search.py`. The one worth understanding rather than just running: `test_upload_and_cross_project_isolation` in `test_projects.py` uploads different real content to two real (temp-path) Chroma collections through the actual HTTP endpoints, then asserts the two collections' contents are disjoint — this is the system's single most important correctness property, tested directly rather than assumed.

Tests use a fake embedding model (`.encode()` stub) so they run without downloading `sentence-transformers`' model or needing Ollama — `init_retrieval` is monkeypatched to a no-op per-test.

## Design Notes

- **Load-once-at-startup, not per-request.** `retrieval.init_retrieval()` runs exactly once, from `main.py`'s lifespan handler. Every route reuses the same module-level Chroma client and embedding model.
- **Isolation by collection naming, not by database.** Every project gets its own Chroma collection named `project_{project_id}`; there's deliberately no code path that queries across collections.
- **Refusal happens before generation, not after.** `generation.is_grounded_enough()` is checked before any Ollama call — an unanswerable question never reaches the LLM.
- **Ollama failures degrade gracefully.** `generation.generate()` catches connection/model errors and returns a descriptive string instead of raising — a missing local Ollama install produces a readable 200 response, not a 500.
