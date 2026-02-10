# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-09
**Commit:** f34c217
**Branch:** main

## OVERVIEW
FASTVOLT is a local FastAPI app that parses FCS files and generates A4 PDF reports, with a static Vue/Tailwind frontend served by the backend.

## STRUCTURE
```
FASTVOLT/
├── backend/               # FastAPI app, services, models, tests
│   ├── app/
│   │   ├── main.py         # API routes + static frontend serving
│   │   ├── models.py       # Pydantic models for FCS metadata
│   │   └── services/       # parser.py, pdf_renderer.py
│   └── tests/              # pytest suite
├── frontend/              # Static SPA (index.html + assets/style.css)
├── specs/                 # Feature specs (plan/spec/tasks/contracts)
├── .specify/              # SpecKit templates and scripts
└── .gemini/               # Speckit command configs
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| API endpoints | backend/app/main.py | /api/parse, /api/export/pdf, /api/export/pdf/zip |
| FCS parsing | backend/app/services/parser.py | flowio parsing + compensation + instrument info |
| PDF layout | backend/app/services/pdf_renderer.py | ReportLab A4 report layout |
| Data models | backend/app/models.py | FCSMetadata, ChannelInfo, InstrumentInfo |
| Frontend UI | frontend/index.html | Vue 3 CDN + Tailwind CSS |
| Frontend styles | frontend/assets/style.css | custom CSS |
| Tests | backend/tests/ | pytest, TestClient, mocks |
| Feature specs | specs/ | spec/plan/tasks per feature |

## CONVENTIONS
- Run locally with `python main.py` (starts uvicorn on 127.0.0.1:8000, reload enabled).
- Frontend is served by FastAPI at `/` with static assets under `/assets`.
- Tests live under `backend/tests/` and use pytest defaults (no config files).
- Dependencies are tracked in `requirements.txt` only (no pyproject.toml).

## ANTI-PATTERNS (THIS PROJECT)
- Avoid reintroducing PNG/CSV export paths; specs mark these as deprecated/removed.
- Do not keep sample items when using SpecKit templates under `.specify/templates/`.

## UNIQUE STYLES
- Spec-driven workflow: feature documentation under `specs/` with plan/spec/tasks files.
- Runtime convenience: `main.py` auto-installs reportlab if missing.

## COMMANDS
```bash
pip install -r requirements.txt
python main.py
pytest backend/tests/
```

## NOTES
- LSP not available by default (basedpyright not installed).
- Frontend uses CDN Vue/Tailwind and hardcoded API base `http://127.0.0.1:8000`.
