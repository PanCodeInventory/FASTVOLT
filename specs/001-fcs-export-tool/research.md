# Research & Technical Decisions: FCS Data Export Tool

**Feature**: `001-fcs-export-tool`
**Date**: 2025-12-22
**Status**: Completed

## 1. FCS Parsing Library (Python)

**Decision**: **flowio**

**Rationale**:
- **Performance**: `flowio` is highly optimized for reading FCS files, especially headers and text segments where voltage/compensation/instrument data reside.
- **Maintenance**: Actively maintained and supports standard FCS versions (2.0, 3.0, 3.1).
- **Dependencies**: Lightweight compared to full analysis suites.
- **Capability**: Provides direct access to the KEY-VALUE pairs in the TEXT segment, which is exactly where `$VOLTAGE`, `$SPILLOVER`, and instrument keys (`$MODEL`, `$CYTSN`, `$CYT`) are stored.

**Alternatives Considered**:
- **fcsparser**: Good, but often bundled with heavier dependencies or older/unmaintained.
- **FlowCytometryTools**: Too heavy; includes analysis logic we don't need (we only need metadata extraction).
- **Manual Parsing**: Error-prone due to binary format variations (big/little endian, different bit depths).

## 2. Visualization & Export (PNG)

**Decision**: **matplotlib** (Backend)

**Rationale**:
- **Header Layout**: `matplotlib`'s `Figure` and `GridSpec` capabilities allow us to construct a complex layout with a dedicated "Header" section (text/metadata) above the data tables.
- **Static Export**: It is the gold standard for generating high-quality static images in Python.
- **Lab Notebook Ready**: We can precisely control font sizes, table borders, and alignment to mimic a formal lab report.

**Alternatives Considered**:
- **Plotly**: Good for interactive web, but static image export (especially with custom headers mixed with tables) is trickier and requires heavy dependencies like `kaleido`.
- **ReportLab**: Excellent for PDFs, but generating a single PNG image from it is less direct than `matplotlib`.

## 3. Application Architecture (Local Web App)

**Decision**: **FastAPI** (Backend) + **Vue.js** (Frontend - embedded)

**Rationale**:
- **FastAPI**: Modern, fast, and provides automatic OpenAPI docs.
- **Vue.js**: Lightweight, easy to embed as a single HTML/JS file (`index.html`) served by FastAPI static files. This simplifies distribution (user just runs `python main.py`).
- **Local Execution**: The user runs a Python script, which starts the server and opens the browser.

**Alternatives Considered**:
- **Electron**: Too heavy for a simple Python-centric tool.
- **Streamlit**: Very easy, but "Intuitive UI" with specific card headers and custom interactions is harder to style than a clean Vue app.

## 4. Batch Processing Strategy

**Decision**: **ZIP Archive Export**

**Rationale**:
- **User Experience**: Downloading one ZIP file is cleaner than 20 separate PNG downloads.
- **Implementation**: Python's `zipfile` module allows creating ZIP archives in-memory (`io.BytesIO`), which can be streamed directly to the user via FastAPI `Response`.

## 5. Directory Structure

We will use a standard "Single Project" structure but separated into `backend` and `frontend` to keep concerns clean.

```text
backend/
  app/
    main.py        # Entry point & API routes
    services/
      parser.py    # flowio wrapper
      renderer.py  # matplotlib logic
    models.py      # Pydantic models
frontend/
  index.html       # Main Vue app
  assets/          # JS/CSS
```