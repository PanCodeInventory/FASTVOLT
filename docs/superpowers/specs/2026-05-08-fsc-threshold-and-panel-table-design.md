# Feature Design: FSC Threshold Display & Editable Panel Table

**Created**: 2026-05-08
**Status**: Approved Design
**Input**: User request to add (1) FSC Threshold display and (2) an editable fluorophore-sample table (panel design) to the FASTVOLT application.

## Overview

Two enhancements to the FASTVOLT FCS Export Tool:

1. **FSC Threshold Display**: Extract the FSC threshold value from FCS files and display it in the voltage table.
2. **Editable Panel Table**: Add an in-browser editable CSV-style table (fluorophore-sample mapping) that users can fill in and export appended to the PDF report.

---

## Feature 1: FSC Threshold

### Data Source

FCS files store threshold information in instrument-specific keywords:

| Instrument | Keyword | Format | Example |
|-----------|---------|--------|---------|
| BD (Fortessa LSRII) | `threshold` | `PARAM, VALUE` | `threshold: FSC,15000` |
| Beckman (CytoFLEX) | `ch{id}th` | Per-channel threshold | `ch1th: 10000`, `ch1id: FSC` |
| Beckman (CytoFLEX) | `pchid` | Primary threshold parameter | `pchid: FSC` |

### Extraction Logic

Priority-based lookup in FCS text metadata:

1. Look for `threshold` key → parse as `PARAM_NAME, VALUE` → find row where `PARAM_NAME` contains "FSC"
2. Look for `pchid` = "FSC" → find `ch{id}th` for matching channel ID
3. Look for any `ch{id}th` where `ch{id}id` = "FSC"

### Data Model

Add to `FCSMetadata` model:

```python
class FCSMetadata(BaseModel):
    # ... existing fields ...
    fsc_threshold: Optional[float] = None  # NEW
```

### Display (UI)

- **Frontend**: In the Channels & Voltages table, add a final row at the bottom with:
  - Column 1: "FSC Threshold"
  - Column 2: (empty or "-")
  - Column 3: the numeric value, formatted with comma separator (e.g., "15,000")
  - Styling: green/emphasized background to distinguish from channel data

- **PDF**: In the Voltage Table section, add the same summary row at the bottom with a distinct style (lighter background, bold text).

---

## Feature 2: Editable Panel Table (荧光-样品表)

### Purpose

A free-form editable table that allows researchers to document their panel design — mapping fluorophores to antibodies/samples for each tube in the experiment. This replaces manual handwriting on printed forms.

### Table Structure

Two-level header, rendered as HTML `<table>` with merged cells:

**Header Row 1** (merged cells):
- `SIGNAL` — spans columns NO. + Fluor. (2 columns)
- `FL1`, `FL2`, ..., `FLN` — one column per fluorescence channel (N varies per instrument)
- `Comments` — free text notes column

**Header Row 2** (sub-labels):
- `NO.` — row number
- `Fluor.` — sample/fluorophore description
- Under each FL column: the fluorophore name extracted from FCS (e.g., "FITC" for FL1), rendered as a lighter reference label

### Data Model

```python
class PanelTable(BaseModel):
    columns: List[str]  # FL1, FL2, ..., FLN
    fluorophore_labels: List[Optional[str]]  # FITC, PE, ... (one per FL col, may be None)
    rows: List[List[Optional[str]]]  # Each row: [NO, Fluor, FL1_val, FL2_val, ..., FLN_val, Comments]
```

Add to `FCSMetadata`:

```python
class FCSMetadata(BaseModel):
    # ... existing fields ...
    panel_table: Optional[PanelTable] = None  # NEW
```

### FL Column Auto-Detection

When parsing an FCS file, detect which parameters are fluorescence channels vs. scatter/time:

| Category | Examples | Include? |
|----------|----------|----------|
| Fluorescence channels | FL1-A, FL2-H, FITC-A, PE-A, APC-Cy7-A, V421-A, etc. | ✅ Yes |
| Scatter parameters | FSC-A, FSC-H, SSC-A, SSC-W, etc. | ❌ No |
| Time | Time | ❌ No |

**Detection rule**: A channel is a fluorescence channel (included as an FL column) if:
- Its name does NOT start with "FSC" or "SSC" (case-insensitive)
- Its name does NOT contain "Time" or "Width" (case-insensitive)
- This covers all PMT-based channels (FL1-A, FL2-H, FITC-A, PE-A, V421-A, etc.)

**Sub-header labels**: The fluorophore name (second header row) is extracted from:
- The channel's label (`$PnS` keyword) if available (e.g., "FITC-A" with label "FITC")
- Otherwise, use the channel name's base fluorophore part (strip suffix like -A, -H)
- If no fluorophore name can be determined, leave the sub-header cell empty

### User Interaction (Frontend)

- The panel table appears below the voltage/compensation display in the file card
- Initially shows an empty table (except NO. column) with correct FL column count and sub-header labels
- Users can:
  - **Edit any cell** by clicking and typing (inline `<input>`)
  - **Add row**: Click "+" button to append a blank row (NO. auto-assigned)
  - **Delete row**: Click "✕" on a row to remove it (NO. column re-numbers)
- **NO. column**: auto-numbered by the frontend (1, 2, 3...) based on row position; not user-editable
- **All other columns** (Fluor., FL1~FLN, Comments): initially empty, user fills in manually

### CSV Import

The table should accept pasted CSV/clipboard data:
- "📋 Paste from CSV" button
- Opens a `<textarea>` overlay where user pastes tabular data
- Parses TSV/CSV and populates the table

### PDF Export

The panel table is appended at the end of the PDF report, after:
1. Header (Institute name)
2. Experiment Info (blank lines)
3. FCS Metadata (instrument, date, filename)
4. Voltage Table (with FSC Threshold row)
5. Compensation Matrix
6. **Panel Table** (NEW — added here)

The PDF table should:
- Use the same two-level header structure
- Auto-shrink font size if table is large
- Fit on the same page if possible, or wrap to next page

---

## Implementation Steps

### Step 1: Backend Data Models (`backend/app/models.py`)

- Add `fsc_threshold: Optional[float]` to `FCSMetadata`
- Add `PanelTable` model class
- Add `panel_table: Optional[PanelTable]` to `FCSMetadata`

### Step 2: FCS Parser (`backend/app/services/parser.py`)

- Add threshold extraction function
- Add fluorescence channel detection and FL column label extraction
- Return both via FCSMetadata

### Step 3: PDF Renderer (`backend/app/services/pdf_renderer.py`)

- Add FSC threshold row to voltage table
- Add panel table rendering at the end of the report

### Step 4: Frontend UI (`frontend/index.html`)

- Add FSC threshold row to voltage table display
- Add editable panel table component
- Add "+" / "✕" row actions
- Add "Paste from CSV" functionality
- Wire panel table data into export request

### Step 5: Tests

- Update `test_parser.py`: test threshold extraction for both BD and CytoFLEX formats
- Update `test_pdf.py`: verify PDF contains panel table
- Update `test_api.py`: verify panel table round-trips through API

---

## File Changes Summary

| File | Change |
|------|--------|
| `backend/app/models.py` | Add `fsc_threshold` field, add `PanelTable` model |
| `backend/app/services/parser.py` | Add threshold extraction, FL column detection |
| `backend/app/services/pdf_renderer.py` | Add threshold row + panel table to PDF |
| `frontend/index.html` | Add threshold display + editable panel table UI + CSV paste |
| `backend/tests/test_parser.py` | Add threshold tests |
| `backend/tests/test_pdf.py` | Add panel table PDF test |
| `backend/tests/test_api.py` | Add panel table API test |

---

## Open Questions (Resolved)

- ~~FSC Threshold display location~~ → **B**: voltage table bottom row ✅
- ~~Panel table columns~~ → NO. / Fluor. / FL1~FLN / Comments ✅
- ~~FL column range~~ → fluorescence channels only, exclude FSC/SSC/Time ✅
- ~~Pre-fill data?~~ → No, all user-entered ✅
- ~~FL column count~~ → Auto-adjusts based on instrument channels ✅
