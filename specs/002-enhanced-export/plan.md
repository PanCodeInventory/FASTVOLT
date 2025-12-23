# Implementation Plan: Enhanced FCS Export

**Branch**: `002-enhanced-export` | **Date**: 2025-12-22 | **Spec**: `specs/002-enhanced-export/spec.md`
**Input**: Feature specification from `/specs/002-enhanced-export/spec.md`

## Summary

This feature replaces existing PNG/CSV exports with a professional A4 PDF lab record. It includes a specific institutional header ("Institute of Immunology, USTC..."), blank lines for manual metadata entry, and auto-extracted instrument details.

Technical Approach:
- **Engine**: `ReportLab` (Platypus) for precise A4 multi-page document generation.
- **Layout**: Portrait orientation, flowing tables for voltages and compensation.
- **UI**: Switch all export buttons from PNG/CSV to PDF.

## Technical Context

**Language/Version**: Python 3.10+, HTML/JS
**Primary Dependencies**: ReportLab, FastAPI, flowio
**Storage**: N/A (Transient processing)
**Testing**: pytest (PDF generation logic), manual layout verification
**Target Platform**: Local Web Application
**Project Type**: Document Generation Feature
**Performance Goals**: PDF generation < 500ms per file.
**Constraints**: A4 strict dimensions (210x297mm).

## Constitution Check

- **Principle 1 (Library-First)**: [CHECK] PDF generation logic will be encapsulated in `pdf_renderer.py`.
- **Principle 3 (Test-First)**: [CHECK] Unit tests will verify PDF structure and metadata inclusion.

## Project Structure

### Documentation

```text
specs/002-enhanced-export/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
```

### Source Code

```text
backend/
├── app/
│   ├── services/
│   │   ├── pdf_renderer.py  # NEW: ReportLab logic
│   └── main.py              # UPDATE: New PDF endpoints
└── tests/
    └── test_pdf.py          # NEW: Generation tests

frontend/
├── index.html               # UPDATE: UI button changes
└── app.js                   # UPDATE: Endpoint mapping
```

**Structure Decision**: Add `pdf_renderer.py` to keep the codebase modular.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | | |