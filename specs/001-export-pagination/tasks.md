# Tasks: Conditional A4 Export Pagination

**Feature Branch**: `001-export-pagination`
**Feature Name**: Conditional A4 Export Pagination

## Phase 1: Setup
*Goal: Initialize environment and ensure base service is ready for modification.*

- [X] T001 Verify `reportlab` installation and current `pdf_renderer.py` functionality in `backend/app/services/pdf_renderer.py`

## Phase 2: Foundational
*Goal: Implement helper logic for height calculation. This is a prerequisite for both user stories.*

- [X] T002 Implement helper function to calculate available print height on A4 page (A4 height minus margins) in `backend/app/services/pdf_renderer.py`
- [X] T003 Refactor `generate_pdf_report` to instantiate `Table` objects (Header, Info, Metadata, Voltage) *before* building the story to allow height inspection in `backend/app/services/pdf_renderer.py`
- [X] T004 Implement logic to calculate the cumulative height of all sections *except* the Compensation Matrix using `.wrap()` in `backend/app/services/pdf_renderer.py`

## Phase 3: User Story 1 - Single Page Export (P1)
*Goal: Ensure small reports fit on a single page without aggressive scaling.*

**Story Goal**: Fit content on one page if space allows.
**Independent Test**: Load small FCS file -> Export -> Verify 1 page PDF.

- [X] T005 [US1] Relax the existing aggressive scaling logic (e.g., minimum font size 8pt instead of 6pt) in `backend/app/services/pdf_renderer.py`
- [X] T006 [US1] Implement conditional logic: IF (Current Height + Matrix Height) <= Printable Height THEN add Matrix directly to story in `backend/app/services/pdf_renderer.py`
- [X] T007 [US1] Verify single-page export works for small datasets (manual verification)

## Phase 4: User Story 2 - Split Page Export (P2)
*Goal: Move Compensation Matrix to Page 2 when content exceeds Page 1 limits.*

**Story Goal**: Prevent clipping by splitting pages.
**Independent Test**: Load large FCS file -> Export -> Verify 2 page PDF with Matrix on page 2.

- [X] T008 [US2] Implement conditional logic: IF (Current Height + Matrix Height) > Printable Height THEN insert `PageBreak()` before Matrix in `backend/app/services/pdf_renderer.py`
- [X] T009 [US2] Ensure Compensation Matrix starts at the top of Page 2 (proper flow handling) in `backend/app/services/pdf_renderer.py`
- [X] T010 [US2] Verify multi-page export works for large datasets (manual verification)

## Phase 5: Polish & Cross-Cutting
*Goal: Final cleanup and edge case handling.*

- [X] T011 [P] Add logging for page split decisions (e.g., "Single page fit" vs "Split page triggered") in `backend/app/services/pdf_renderer.py`
- [X] T012 Verify handling of extremely large voltage tables (that might fill Page 1 alone) ensuring graceful overflow in `backend/app/services/pdf_renderer.py`

## Dependencies

1. **T001 (Setup)** -> T002
2. **T002, T003, T004 (Foundational)** -> T005, T006 (US1)
3. **T006 (US1)** -> T008 (US2) (Logic builds upon the conditional check)
4. **T008 (US2)** -> T011, T012 (Polish)

## Implementation Strategy
- **MVP**: Complete T001-T007. This delivers the "Single Page" optimization and prepares the logic for the split.
- **Full Feature**: Complete T008-T010. This enables the specific "Matrix on Page 2" behavior requested.
- **Parallelization**: T011 (Logging) can be done anytime after T008.
