# Implementation Tasks: FCS Data Export Tool

**Feature**: `001-fcs-export-tool`
**Spec**: `specs/001-fcs-export-tool/spec.md`
**Status**: Pending

## Phase 1: Setup
*Goal: Initialize project structure and dependencies.*

- [x] T001 Create project directories (backend/app, backend/tests, frontend/assets)
- [x] T002 Create `requirements.txt` with fastapi, uvicorn, python-multipart, flowio, matplotlib, pandas
- [x] T003 [P] Create `backend/app/main.py` with basic FastAPI app and CORS setup
- [x] T004 [P] Create `frontend/index.html` with basic Vue.js CDN setup and container layout
- [x] T005 Create `backend/tests/conftest.py` for pytest configuration

## Phase 2: Foundational (Core Logic)
*Goal: Implement core FCS parsing and data modeling (Blocking for all stories).*

- [x] T006 [P] Create `backend/app/models.py` defining Pydantic models (FCSMetadata, ChannelInfo, CompensationMatrix) based on data-model.md
- [x] T006a Update `backend/app/models.py` to include `InstrumentInfo` model and `instrument` field in `FCSMetadata`
- [x] T007 Create `backend/app/services/parser.py` with `parse_fcs` function using `flowio`
- [x] T007a Update `backend/app/services/parser.py` to extract Instrument Metadata ($MODEL, $CYTSN, $CYT)
- [x] T008 Implement `extract_channels` logic in `parser.py` to get names and voltages
- [x] T009 Implement `extract_spillover` logic in `parser.py` to get compensation matrix
- [x] T010 [P] Create `backend/tests/test_parser.py` with unit tests for `parse_fcs` using a sample .fcs file (mocked or real)
- [x] T010a Update `backend/tests/test_parser.py` to verify instrument metadata extraction

## Phase 3: User Story 1 - Load and View FCS Data (Priority: P1)
*Goal: Allow users to upload FCS files and see the data in the browser.*
*Test Criteria: Upload a file -> JSON response contains correct voltage/compensation.*

- [x] T011 [US1] Create `POST /api/parse` endpoint in `backend/app/main.py` that accepts file upload
- [x] T012 [US1] Implement `parse_fcs` service call in the API endpoint and return `List[FCSMetadata]`
- [x] T013 [P] [US1] Create `backend/tests/test_api.py` to test `/api/parse` with multipart upload
- [x] T014 [US1] Implement file drag-and-drop zone in `frontend/index.html` (or `app.js`)
- [x] T015 [US1] Implement Vue method to `POST` file to `/api/parse` and store response in `data` variable
- [x] T016a [US1] Update `frontend/index.html` file card to show Instrument Info (Model, SN) in header
- [x] T016 [US1] Create Voltage Table component/HTML structure in `frontend/index.html` to display channel data
- [x] T017 [US1] Create Compensation Matrix Table component/HTML structure in `frontend/index.html`

## Phase 4: User Story 2 - Export Data to Image (PNG) (Priority: P2)
*Goal: Generate static PNGs of the data tables for lab notebooks.*
*Test Criteria: Request PNG -> Receive binary image with timestamp.*

- [x] T018 [US2] Create `backend/app/services/renderer.py` for Matplotlib image generation
- [x] T018a [US2] Update `backend/app/services/renderer.py` to include Instrument Header in PNG layout
- [x] T019 [US2] Implement `generate_voltage_table_plot` function in `renderer.py`
- [x] T020 [US2] Implement `generate_compensation_matrix_plot` function in `renderer.py`
- [x] T021 [US2] Implement `combine_plots_with_timestamp` to create final PNG image
- [x] T022 [US2] Create `POST /api/export/png` endpoint that accepts `FCSMetadata` (or ID) and returns `image/png`
- [x] T023 [P] [US2] Add "Export PNG" button in `frontend/index.html` for each file card
- [x] T024 [US2] Connect frontend button to `/api/export/png` and trigger browser download

## Phase 5: Removed (CSV Export)
*Goal: CSV export was removed from scope in favor of PNG focus.*

- [x] T025 [P] [US3] (Legacy) Create `POST /api/export/csv` endpoint in `backend/app/main.py`
- [x] T026 [US3] (Legacy) Implement CSV generation logic
- [x] T027 [US3] (Legacy) Add "Export CSV" button in `frontend/index.html`
- [x] T028 [US3] (Legacy) Connect frontend button to `/api/export/csv`

## Phase 6: Polish & Batch Processing
*Goal: Final cleanup and batch export support.*

- [x] T029 [P] Implement `POST /api/export/zip` for batch export of multiple files
- [x] T030 Update frontend to support selecting multiple files for "Batch Export"
- [x] T031 Add error handling in frontend (display error messages from API)
- [x] T032 Style tables and buttons with CSS (`frontend/style.css`) to meet "Intuitive UI" requirement

## Dependencies

1. **Phase 2 (Foundation)** MUST complete before **Phase 3 (View)**.
2. **Phase 3 (View)** MUST complete before **Phase 4 (PNG)** and **Phase 5 (CSV)** (requires parsed data).
3. **Phase 4** and **Phase 5** can be executed in parallel.

## Implementation Strategy

- **MVP (Phase 1-3)**: Deliver a working tool that parses and displays data. Verification: Open app, drag file, see table.
- **V1 (Phase 4-5)**: Add export capabilities. Verification: Download PNG/CSV and check contents.
- **V1.1 (Phase 6)**: Polish UI and add batch ZIP export.
