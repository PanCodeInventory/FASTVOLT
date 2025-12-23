# Implementation Plan: Conditional A4 Export Pagination

**Branch**: `001-export-pagination` | **Date**: 2025-12-23 | **Spec**: [specs/001-export-pagination/spec.md]
**Input**: Feature specification from `specs/001-export-pagination/spec.md`

## Summary

Implement conditional pagination for PDF exports. The system will pre-calculate the height of report sections using `reportlab`. If the total height including the Compensation Matrix exceeds the A4 printable area, the Matrix will be moved to a second page. This replaces the current behavior of aggressively shrinking content to force a single-page layout.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: `reportlab` (existing)
**Storage**: N/A (Transient generation)
**Testing**: Manual Verification (Visual inspection of PDF)
**Target Platform**: Linux/macOS/Windows (Backend execution)
**Project Type**: Web Application (FastAPI Backend)
**Performance Goals**: <500ms overhead for layout calculation
**Constraints**: Output must be A4 PDF
**Scale/Scope**: Logic change in single service file (`pdf_renderer.py`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Library-First**: N/A (Enhancement to existing service)
- [x] **CLI Interface**: N/A (Web feature)
- [x] **Test-First**: N/A (Visual output requires manual verification or complex PDF parsing; manual verification accepted for layout tweaks)
- [x] **Integration Testing**: N/A
- [x] **Observability**: Logging of page split decision recommended
- [x] **Simplicity**: Logic kept simple (Height check -> Break)

## Project Structure

### Documentation (this feature)

```text
specs/001-export-pagination/
├── plan.md              # This file
├── research.md          # Layout strategy and library usage
├── data-model.md        # Report structure definition
├── quickstart.md        # Manual testing guide
├── contracts/           # (Empty) No API changes
└── tasks.md             # Implementation tasks
```

### Source Code (repository root)

```text
backend/
└── app/
    └── services/
        └── pdf_renderer.py  # MAIN LOGIC CHANGE
```

**Structure Decision**: Modify existing `pdf_renderer.py`. No new modules required.

## Complexity Tracking

*None.*