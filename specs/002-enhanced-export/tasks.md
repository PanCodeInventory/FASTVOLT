# Implementation Tasks: Enhanced FCS Export

**Feature**: `002-enhanced-export`
**Spec**: `specs/002-enhanced-export/spec.md`
**Status**: Completed

## Phase 1: Setup
*Goal: Prepare environment for PDF generation.*

- [x] T001 Update `requirements.txt` to include `reportlab`
- [x] T002 [P] Create `backend/app/services/pdf_renderer.py` placeholder
- [x] T003 Create `backend/tests/test_pdf.py` for PDF generation tests

## Phase 2: PDF Renderer Service (Core)
*Goal: Implement the logic to generate A4 PDFs with the required layout.*

- [x] T004 [P] [US2] Implement `setup_document` in `pdf_renderer.py` (A4 size, margins, simple doc template)
- [x] T005 [US2] Implement `draw_header` function in `pdf_renderer.py` with "Institute of Immunology, USTC..." text
- [x] T006 [US1] Implement `draw_experiment_info` function in `pdf_renderer.py` with blank lines for manual entry
- [x] T007 [US3] Implement `draw_instrument_metadata` function in `pdf_renderer.py` to show Model/Date
- [x] T008 [US2] Implement `draw_voltage_table` function in `pdf_renderer.py` using ReportLab Table
- [x] T009 [US2] Implement `draw_compensation_matrix` function in `pdf_renderer.py` using ReportLab Table
- [x] T010 [US2] Assemble full `generate_pdf_report(metadata)` function in `pdf_renderer.py`
- [x] T011 [P] [US2] Create unit test in `backend/tests/test_pdf.py` to verify PDF byte generation

## Phase 3: API Integration
*Goal: Expose PDF generation via API endpoints.*

- [x] T012 [P] [US2] Update `backend/app/main.py` to import `pdf_renderer`
- [x] T013 [US2] Implement `POST /api/export/pdf` in `backend/app/main.py`
- [x] T014 [US2] Implement `POST /api/export/pdf/zip` endpoint for batch processing in `backend/app/main.py`
- [x] T015 [P] Update `backend/tests/test_api.py` (or create new) to test `/api/export/pdf`

## Phase 4: Frontend UI Updates
*Goal: Update the web interface to use PDF export.*

- [x] T016 [US2] Update `frontend/index.html` card button to "Export PDF" (was PNG)
- [x] T017 [US2] Update `frontend/index.html` batch button to "Export All (PDF ZIP)"
- [x] T018 [US2] Update Vue `exportPDF` function in `frontend/index.html` (script section) to call new endpoint
- [x] T019 [US2] Update Vue `exportBatch` function in `frontend/index.html` to call new zip endpoint

## Phase 5: Cleanup
*Goal: Remove deprecated PNG/CSV code to keep project clean.*

- [x] T020 Remove `backend/app/services/renderer.py` (Old Matplotlib renderer)
- [x] T021 Remove old `/api/export/png` and `/api/export/zip` (PNG version) endpoints from `backend/app/main.py`
- [x] T022 Clean up unused imports in `backend/app/main.py` (matplotlib, etc.)



## Dependencies

1. **Phase 2** (Renderer) is the core dependency for Phase 3 (API).
2. **Phase 3** (API) must exist before Phase 4 (Frontend) can work.
3. **Phase 5** (Cleanup) should be done last to ensure no regression.

## Implementation Strategy

- **Step 1**: Get `reportlab` installed and generating a dummy PDF.
- **Step 2**: Build the layout pieces one by one (Header -> Info -> Tables).
- **Step 3**: Connect the API and Frontend.
- **Step 4**: Verify manual handwriting lines look correct on A4.
