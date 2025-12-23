# Implementation Plan: FCS Data Export Tool

**Branch**: `001-fcs-export-tool` | **Date**: 2025-12-22 | **Spec**: `specs/001-fcs-export-tool/spec.md`
**Input**: Feature specification from `/specs/001-fcs-export-tool/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

The **FCS Data Export Tool** is a local web application designed to parse Flow Cytometry Standard (FCS) files, extracting not just voltages and compensation, but also critical **Instrument Metadata** (Model, Serial Number). It generates publication-quality **PNG reports** with a structured header and supports **Batch ZIP Export**.

Technical Approach:
- **Backend**: Python (FastAPI) for file parsing and image generation.
- **Parsing**: `flowio` library, enhanced to extract `$MODEL`, `$CYTSN`, `$CYT` keys.
- **Visualization**: `matplotlib` with `GridSpec` for a custom "Header + Tables" layout.
- **Frontend**: Vue.js (Lightweight) for an intuitive drag-and-drop interface.
- **Distribution**: Simple `python main.py` execution opening a local browser.

## Technical Context

**Language/Version**: Python 3.10+ (Backend), HTML/JS (Frontend)
**Primary Dependencies**: FastAPI (Web), flowio (Parsing), matplotlib (Rendering), uvicorn (Server)
**Storage**: N/A (Transient processing; exports saved to user disk)
**Testing**: pytest (Backend), manual UI testing (Frontend)
**Target Platform**: Local Desktop (Cross-platform Python)
**Project Type**: Local Web Application
**Performance Goals**: <2s to load 10MB FCS file; <1m to export batch.
**Constraints**: Must run locally without external internet dependency.
**Scale/Scope**: Single user, batch processing ~10-50 files.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle 1 (Library-First)**: [CHECK] Core parsing logic will be separated from API logic.
- **Principle 2 (CLI Interface)**: [CHECK] While this is a GUI tool, the backend structure supports adding a CLI entry point later if needed.
- **Principle 3 (Test-First)**: [CHECK] Pytest will be used for parser and API contracts.

## Project Structure

### Documentation (this feature)

```text
specs/001-fcs-export-tool/
├── plan.md              # This file
├── research.md          # Technology decisions (flowio, matplotlib, FastAPI)
├── data-model.md        # Entity definitions (FCSMetadata, InstrumentInfo, etc.)
├── quickstart.md        # User/Dev running instructions
├── contracts/           # OpenAPI spec
└── tasks.md             # Implementation tasks
```

### Source Code (repository root)

```text
# Local Web App Structure
backend/
├── app/
│   ├── main.py          # FastAPI app & routes
│   ├── services/
│   │   ├── parser.py    # flowio wrapper (Parsing logic)
│   │   └── renderer.py  # matplotlib logic (PNG Generation)
│   └── models.py        # Pydantic models
└── tests/
    ├── test_parser.py
    └── test_api.py

frontend/
├── index.html           # Main Vue app
├── assets/
│   └── style.css
```

**Structure Decision**: Split `backend` and `frontend` to keep Python logic testable and independent of the UI layer.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | | |