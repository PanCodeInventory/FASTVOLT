# Research & Technical Decisions: Enhanced FCS Export

**Feature**: `002-enhanced-export`
**Date**: 2025-12-22
**Status**: Completed

## 1. PDF Generation Library

**Decision**: **ReportLab**

**Rationale**:
- **Precision**: `ReportLab` allows for exact millimeter-level positioning, which is critical for satisfying the A4 (210x297mm) requirement.
- **Table Handling**: `platypus` (part of ReportLab) provides robust table objects that can automatically flow across multiple pages, satisfying **FR-006**.
- **Handwriting Lines**: It is easy to draw graphic lines (`canvas.line`) or use specific border styles in tables to create the "blank lines" for manual entry.
- **Python Native**: It integrates seamlessly with our existing Python backend.

**Alternatives Considered**:
- **FPDF2**: Good and simpler, but less powerful for complex table flows spanning multiple pages.
- **WeasyPrint**: Requires HTML/CSS. While flexible, it has heavier system dependencies (Pango, Cairo) which might complicate local deployment. `ReportLab` is a pure Python (mostly) library with fewer system-level requirements.

## 2. Report Layout Design (A4 Portrait)

**Decision**: **Platypus Flowable Layout**

**Rationale**:
Using `platypus` allows us to define "Flowables" (Paragraphs, Tables, Spacers) that respect margins and page breaks.

**Layout Breakdown (Top-to-Bottom)**:
1.  **Institution Header**: Centered large bold text.
2.  **Experiment Metadata**: A 2-column grid with labels and underlined blank spaces.
3.  **FCS Metadata**: A boxed or grey-shaded section containing extracted Instrument Model and Test Date.
4.  **Voltage Table**: A `Table` object with repeating headers on page breaks.
5.  **Compensation Matrix**: A `Table` object with rotated headers (if wide) and repeating row/col headers.

## 3. Implementation Patterns

**Decision**: **Renderer Service Evolution**

**Rationale**:
We will create a new service `backend/app/services/pdf_renderer.py` rather than replacing `renderer.py` immediately, allowing for a clean transition. The API endpoint `/api/export/pdf` will use this new service.

## 4. UI Transition

**Decision**: **Replace PNG with PDF in UI**

**Rationale**:
Per **FR-003**, the user wants PDF only. We will update the frontend buttons to "Export PDF" and remove the PNG/CSV options to reduce visual clutter.
