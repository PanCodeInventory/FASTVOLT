# Quickstart: Testing Export Pagination

**Feature**: `001-export-pagination`

## Overview
This feature introduces conditional pagination for PDF exports. If the content is too long for a single A4 page, the Compensation Matrix is moved to a second page.

## Prerequisite
Ensure the backend server is running:
```bash
uvicorn backend.app.main:app --reload
```

## Manual Verification

1.  **Small File (Single Page)**
    - Load an FCS file with few channels (e.g., < 10).
    - Click **Export PDF**.
    - **Verify**: The PDF is 1 page. All content fits.

2.  **Large File (Multi Page)**
    - Load an FCS file with many channels (e.g., > 18) or extensive metadata.
    - Click **Export PDF**.
    - **Verify**: The PDF is 2 pages.
    - **Verify**: The "Compensation Matrix (%)" header and table start at the top of Page 2.
    - **Verify**: The Voltage Table ends on Page 1.

## Code Location
- Logic: `backend/app/services/pdf_renderer.py` -> `generate_pdf_report`
