# FSC Threshold & Panel Table Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add FSC threshold display + editable panel table to FASTVOLT

**Architecture:** Backend changes to data models and FCS parser extract threshold + fluorophore metadata; frontend adds inline-editable table and threshold display row; PDF renderer appends both to report output.

**Tech Stack:** Python 3.10+, FastAPI, flowio, ReportLab, Vue 3 (CDN), Tailwind CSS

---

### Task 1: Update Data Models

**Files:**
- Modify: `backend/app/models.py`

- [ ] **Step 1: Add `fsc_threshold` to FCSMetadata**

Add a single optional float field:

```python
class FCSMetadata(BaseModel):
    filename: str
    timestamp: Optional[str] = None
    instrument: Optional[InstrumentInfo] = None
    channels: List[ChannelInfo]
    compensation: Optional[CompensationMatrix] = None
    fsc_threshold: Optional[float] = None  # ADD THIS LINE
    panel_table: Optional["PanelTable"] = None  # ADD THIS LINE (after panel_table class)
    error: Optional[str] = None
```

- [ ] **Step 2: Add PanelTable model class**

Add this class BEFORE FCSMetadata (or use `model_rebuild` / `update_forward_refs`):

```python
class PanelTable(BaseModel):
    """Editable fluorophore-sample panel design table."""
    columns: List[str]                     # ["FL1", "FL2", ..., "FLN"]
    fluorophore_labels: List[Optional[str]]  # ["FITC", "PE", ..., None]
    rows: List[List[Optional[str]]]          # Each row: [NO, Fluor, FL1_val, ..., FLN_val, Comments]
```

Note: NO is auto-numbered by frontend, but stored as first column element for PDF rendering.

---

### Task 2: Parser — FSC Threshold Extraction

**Files:**
- Modify: `backend/app/services/parser.py`

- [ ] **Step 1: Add threshold extraction helper function**

Add a function before `parse_fcs`:

```python
def extract_threshold(text: Dict[str, str]) -> Optional[float]:
    """Extract FSC threshold from FCS text metadata.
    
    Priority:
    1. BD format: threshold = "FSC,15000" (key='threshold')
    2. CytoFLEX format: ch1th=10000, ch1id=FSC, pchid=FSC
    """
    # 1. Check BD-style 'threshold' key
    threshold_val = text.get('threshold')
    if threshold_val:
        parts = threshold_val.split(',')
        if len(parts) == 2:
            param_name, value_str = parts[0].strip(), parts[1].strip()
            if 'FSC' in param_name.upper():
                try:
                    return float(value_str)
                except ValueError:
                    pass
    
    # 2. Check CytoFLEX-style per-channel thresholds
    # Find which channel is FSC
    fsc_ch_id = None
    for key, val in text.items():
        if key.endswith('id') and val.upper() == 'FSC':
            # Extract channel number from key (e.g., 'ch1id' -> '1')
            ch_num = key.replace('ch', '').replace('id', '')
            fsc_ch_id = ch_num
            break
    
    if fsc_ch_id:
        # Look for ch{X}th
        th_key = f'ch{fsc_ch_id}th'
        if th_key in text:
            try:
                return float(text[th_key])
            except ValueError:
                pass
    
    # Also check pchid/pchtp (primary threshold parameter)
    if text.get('pchid', '').upper() == 'FSC':
        # Try all ch{X}th keys for the one matching FSC
        for key, val in text.items():
            if key.endswith('th'):
                ch_num = key.replace('ch', '').replace('th', '')
                id_key = f'ch{ch_num}id'
                if text.get(id_key, '').upper() == 'FSC':
                    try:
                        return float(val)
                    except ValueError:
                        pass
    
    return None
```

- [ ] **Step 2: Call threshold extraction in parse_fcs**

Inside `parse_fcs`, after parsing channels and before returning, add:

```python
# 5. Extract FSC Threshold
fsc_threshold = extract_threshold(text)
print(f"DEBUG: Extracted FSC Threshold: {fsc_threshold}")
```

Then add to the return statement:

```python
return FCSMetadata(
    filename=filename,
    timestamp=timestamp,
    instrument=instrument,
    channels=channels,
    compensation=compensation,
    fsc_threshold=fsc_threshold,
    panel_table=None  # Will be set in Task 3
)
```

---

### Task 3: Parser — FL Channel Detection & PanelTable Initialization

**Files:**
- Modify: `backend/app/services/parser.py`

- [ ] **Step 1: Add panel table building logic**

After extracting threshold, add:

```python
# 6. Build PanelTable skeleton (columns and fluorophore labels)
panel_table = build_panel_table(text, channels)
print(f"DEBUG: PanelTable columns: {panel_table.columns if panel_table else 'None'}")
```

- [ ] **Step 2: Add build_panel_table helper function**

```python
def build_panel_table(text: Dict[str, str], channels: List[ChannelInfo]) -> Optional[PanelTable]:
    """Build a PanelTable skeleton from FCS metadata.
    
    Detects fluorescence channels (excludes FSC, SSC, Time, Width)
    and extracts fluorophore labels for the second header row.
    """
    # Strategy 1: Use compensation fluorochrome list if available
    fluorochromes = []
    
    # Try spillover/spill keys first (gives clean fluorochrome list)
    for key in ['spillover', 'spill', '$SPILLOVER', '$SPILL']:
        if key in text:
            spill_str = text[key]
            parts = spill_str.split(',')
            if len(parts) > 0:
                try:
                    n = int(parts[0])
                    fluorochromes = [f.strip() for f in parts[1:n+1]]
                    break
                except (ValueError, IndexError):
                    continue
    
    # Try CytoFLEX compchh/compcha keys
    if not fluorochromes:
        for key in ['compchh', 'compcha']:
            if key in text:
                fluorochromes = text[key].split()
                if fluorochromes:
                    break
    
    # Strategy 2: Derive from channel names
    if not fluorochromes:
        for ch in channels:
            name = ch.name or ''
            # Skip scatter, time, width
            if any(name.upper().startswith(p) for p in ['FSC', 'SSC']):
                continue
            if 'TIME' in name.upper() or 'WIDTH' in name.upper():
                continue
            # Strip -A, -H, -W suffix for dedup
            base = name
            for suffix in ['-A', '-H', '-W']:
                if base.upper().endswith(suffix.upper()):
                    base = base[:-len(suffix)]
                    break
            if base not in fluorochromes:
                fluorochromes.append(base)
    
    if not fluorochromes:
        return None
    
    # Build column labels
    columns = [f"FL{i+1}" for i in range(len(fluorochromes))]
    
    # Clean fluorophore names for display (strip -A, -H, -W suffixes)
    clean_labels = []
    for fc in fluorochromes:
        clean = fc
        for suffix in ['-A', '-H', '-W']:
            if clean.upper().endswith(suffix.upper()):
                clean = clean[:-len(suffix)]
                break
        clean_labels.append(clean)
    
    return PanelTable(
        columns=columns,
        fluorophore_labels=clean_labels,
        rows=[]
    )
```

- [ ] **Step 3: Update parse_fcs return to include panel_table**

Return statement should now include `panel_table=panel_table`.

Make sure `PanelTable` is imported at the top:

```python
from ..models import FCSMetadata, ChannelInfo, CompensationMatrix, InstrumentInfo, PanelTable
```

---

### Task 4: PDF Renderer — FSC Threshold Row

**Files:**
- Modify: `backend/app/services/pdf_renderer.py`

- [ ] **Step 1: Add FSC threshold row to voltage table**

After building `vol_rows` from channel data, add threshold row if value exists:

```python
# Add FSC Threshold row if present
if metadata.fsc_threshold is not None:
    threshold_str = f"{metadata.fsc_threshold:,.0f}"  # e.g., "15,000"
    vol_rows.append(["FSC Threshold", "-", threshold_str])
```

- [ ] **Step 2: Style the threshold row**

Update the TableStyle for vol_table to style the threshold row differently:

```python
# Add alternating row coloring (applies to channels only)
('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.whitesmoke]),
# Style the FSC Threshold row (last row) if present
```

After building `vol_table`, conditionally add a green background for the last row:

```python
if metadata.fsc_threshold is not None:
    last_row_idx = len(vol_rows) - 1
    vol_table.setStyle(TableStyle([
        ('BACKGROUND', (0, last_row_idx), (-1, last_row_idx), colors.HexColor('#f0fdf4')),
        ('TEXTCOLOR', (0, last_row_idx), (-1, last_row_idx), colors.HexColor('#166534')),
        ('FONTNAME', (0, last_row_idx), (-1, last_row_idx), 'Helvetica-Bold'),
        ('LINEABOVE', (0, last_row_idx), (-1, last_row_idx), 1, colors.HexColor('#86efac')),
    ]))
```

---

### Task 5: PDF Renderer — Panel Table

**Files:**
- Modify: `backend/app/services/pdf_renderer.py`

- [ ] **Step 1: Add panel table rendering**

After the compensation matrix section (step 6 in existing code), add:

```python
# 7. Panel Table (Fluorophore-Sample Design)
if metadata.panel_table and metadata.panel_table.rows:
    elements.append(Paragraph("Panel Design (Fluorophore-Sample)", section_title_style))
    
    pt = metadata.panel_table
    n_fl_cols = len(pt.columns)
    total_cols = 2 + n_fl_cols + 1  # NO + Fluor + FL1..FLN + Comments
    
    # Build table data
    table_data = []
    
    # Header row 1: SIGNAL | FL1 | FL2 | ... | FLN | Comments
    h1 = ["SIGNAL", ""] + list(pt.columns) + ["Comments"]
    table_data.append(h1)
    
    # Header row 2: NO. | Fluor. | label1 | label2 | ... | ""
    h2 = ["NO.", "Fluor."]
    for lbl in pt.fluorophore_labels:
        h2.append(lbl if lbl else "")
    h2.append("")
    table_data.append(h2)
    
    # Data rows
    for row in pt.rows:
        table_data.append(list(row))
    
    # Calculate column widths
    col_widths = [1.2*cm, 2.5*cm]  # NO, Fluor
    for _ in range(n_fl_cols):
        col_widths.append(19*cm / max(total_cols, 1))  # Dynamic per FL column
    col_widths.append(2.0*cm)  # Comments
    
    panel_font = max(6, font_size - 2)
    
    panel_table = Table(table_data, colWidths=col_widths, repeatRows=2)
    panel_table.setStyle(TableStyle([
        # Header row 1 styling
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4a86e8')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), panel_font),
        # Merge SIGNAL cell (col 0-1 in row 0)
        ('SPAN', (0,0), (1,0)),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        # Header row 2 styling
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#e8f0fe')),
        ('FONTSIZE', (0,1), (-1,1), panel_font - 1),
        # Grid
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        # Row backgrounds
        ('ROWBACKGROUNDS', (0,2), (-1,-1), [colors.white, colors.whitesmoke]),
        # NO column center aligned
        ('ALIGN', (0,2), (0,-1), 'CENTER'),
        # Leading
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    
    # Only add SPAN if SIGNAL cell exists correctly
    # (ReportLab SPAN merges cells: (start_col, start_row) to (end_col, end_row))
    
    elements.append(panel_table)
```

Note: the `total_cols` variable is used only for dynamic width calculation. Fix width calc to use actual number of columns.

- [ ] **Step 2: Create the section title style for the panel table (already exists as section_title_style)**

The `section_title_style` is already defined in the function, so it can be reused.

---

### Task 6: Frontend — FSC Threshold Display

**Files:**
- Modify: `frontend/index.html`

- [ ] **Step 1: Add FSC threshold row to the voltage table template**

In the voltage table section, after the `v-for` loop in `<tbody>`, add a threshold row:

```html
<tbody class="divide-y divide-gray-200">
    <tr v-for="ch in file.channels" :key="ch.name">
        <td class="px-4 py-2 font-mono text-gray-800">{{ ch.name }}</td>
        <td class="px-4 py-2 text-gray-600">{{ ch.label || '-' }}</td>
        <td class="px-4 py-2 text-right font-mono text-blue-600">{{ ch.voltage }}</td>
    </tr>
    <!-- FSC Threshold Row -->
    <tr v-if="file.fsc_threshold !== null && file.fsc_threshold !== undefined"
        class="bg-green-50 border-t-2 border-green-300">
        <td class="px-4 py-2 font-bold text-green-800">FSC Threshold</td>
        <td class="px-4 py-2 text-gray-500">-</td>
        <td class="px-4 py-2 text-right font-mono font-bold text-green-700">
            {{ Number(file.fsc_threshold).toLocaleString() }}
        </td>
    </tr>
</tbody>
```

---

### Task 7: Frontend — Editable Panel Table

**Files:**
- Modify: `frontend/index.html`

- [ ] **Step 1: Add panel table template**

After the compensation matrix section (inside the file card's right column area, or in its own section below), add:

```html
<!-- Panel Table -->
<div v-if="file.panel_table" class="mt-6 col-span-1 lg:col-span-2">
    <h3 class="text-lg font-semibold mb-2 text-gray-700">Panel Design (Fluorophore-Sample)</h3>
    <div class="overflow-x-auto bg-white rounded shadow">
        <table class="min-w-full text-xs border-collapse">
            <!-- Header Row 1 -->
            <thead>
                <tr class="bg-blue-600 text-white">
                    <th colspan="2" class="px-3 py-2 text-center border border-blue-700">SIGNAL</th>
                    <th v-for="col in file.panel_table.columns" :key="'h1-'+col"
                        class="px-3 py-2 text-center border border-blue-700">
                        {{ col }}
                    </th>
                    <th class="px-3 py-2 text-center border border-blue-700">Comments</th>
                </tr>
                <!-- Header Row 2 -->
                <tr class="bg-blue-50">
                    <th class="px-3 py-1 text-center border border-gray-200 font-normal text-gray-500 text-2xs">NO.</th>
                    <th class="px-3 py-1 text-center border border-gray-200 font-normal text-gray-500 text-2xs">Fluor.</th>
                    <th v-for="(lbl, li) in file.panel_table.fluorophore_labels" :key="'h2-'+li"
                        class="px-3 py-1 text-center border border-gray-200 font-normal text-gray-400 text-2xs">
                        {{ lbl || '' }}
                    </th>
                    <th class="px-3 py-1 text-center border border-gray-200 font-normal text-gray-500 text-2xs"></th>
                </tr>
            </thead>
            <!-- Editable Data Rows -->
            <tbody>
                <tr v-for="(row, rIdx) in file.panel_table.rows" :key="rIdx"
                    :class="rIdx % 2 === 0 ? 'bg-white' : 'bg-gray-50'">
                    <td class="px-2 py-1 text-center text-gray-500 text-2xs border border-gray-200">
                        {{ rIdx + 1 }}
                    </td>
                    <td class="px-2 py-1 border border-gray-200">
                        <input v-model="row[1]" 
                               class="w-full border border-gray-300 rounded px-1 py-0.5 text-xs focus:border-blue-400 focus:ring-1 focus:ring-blue-200 outline-none"
                               placeholder="Sample">
                    </td>
                    <td v-for="(val, cIdx) in row.slice(2, row.length - 1)" :key="cIdx"
                        class="px-2 py-1 border border-gray-200">
                        <input v-model="row[cIdx + 2]"
                               class="w-full border border-gray-300 rounded px-1 py-0.5 text-xs focus:border-blue-400 focus:ring-1 focus:ring-blue-200 outline-none"
                               placeholder="-">
                    </td>
                    <td class="px-2 py-1 border border-gray-200">
                        <input v-model="row[row.length - 1]"
                               class="w-full border border-gray-300 rounded px-1 py-0.5 text-xs focus:border-blue-400 focus:ring-1 focus:ring-blue-200 outline-none"
                               placeholder="Notes">
                    </td>
                    <td class="px-2 py-1 border border-gray-200 text-center">
                        <button @click="removePanelRow(file, rIdx)" 
                                class="text-red-400 hover:text-red-600 text-xs font-bold">✕</button>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
    <div class="mt-2 flex gap-2">
        <button @click="addPanelRow(file)" 
                class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-xs transition-colors">
            + 添加行
        </button>
        <button @click="pastePanelCSV(file)" 
                class="bg-gray-200 hover:bg-gray-300 text-gray-700 px-3 py-1 rounded text-xs transition-colors">
            📋 Paste CSV
        </button>
    </div>
</div>
```

- [ ] **Step 2: Add Vue methods for panel table editing**

In the Vue `setup()` function, add methods:

```javascript
const addPanelRow = (file) => {
    if (!file.panel_table) return
    const nCols = file.panel_table.columns.length
    const newRow = ['', '', ...Array(nCols).fill(''), '']  // NO, Fluor, FL1..N, Comments
    file.panel_table.rows.push(newRow)
}

const removePanelRow = (file, idx) => {
    if (!file.panel_table) return
    file.panel_table.rows.splice(idx, 1)
}

const pastePanelCSV = (file) => {
    // Open a textarea for CSV paste
    const text = prompt("Paste CSV/TSV data (tab-separated):\nFirst line = header (ignored)\nFollowing lines = data rows")
    if (!text || !file.panel_table) return
    
    const lines = text.trim().split('\n')
    const nCols = file.panel_table.columns.length
    
    // Skip header line, parse data rows
    for (let i = 1; i < lines.length; i++) {
        const parts = lines[i].split('\t')
        if (parts.length < 2) continue
        
        const row = ['', '', ...Array(nCols).fill(''), '']
        row[1] = parts[0] || ''  // Fluor./Sample column
        for (let j = 1; j < parts.length && j <= nCols; j++) {
            row[j + 1] = parts[j] || ''
        }
        const commentIdx = 2 + nCols
        if (parts.length > nCols + 1) {
            row[commentIdx] = parts.slice(nCols + 1).join(' ')
        }
        file.panel_table.rows.push(row)
    }
}
```

Also expose these in the return statement:

```javascript
return {
    files,
    fileInput,
    loading,
    errorMsg,
    handleFileSelect,
    handleDrop,
    triggerFileInput,
    exportPDF,
    exportBatch,
    addPanelRow,       // ADD
    removePanelRow,    // ADD
    pastePanelCSV      // ADD
}
```

---

### Task 8: Frontend — Wire Panel Table to Export

**Files:**
- Modify: `frontend/index.html`

- [ ] **Step 1: Ensure panel table data is sent with export requests**

The current `exportPDF` and `exportBatch` functions send the whole `file` object (which includes `panel_table`) as JSON. Since Vue reactivity tracks changes to `file.panel_table.rows`, the edited rows will be included automatically. No additional code needed for the serialization — but verify that the `panel_table` isn't excluded by any JSON serialization.

Add a check: When the user clicks export, before sending, log the panel table data:

```javascript
// Add inside exportPDF function, before fetch:
console.log("Exporting with panel_table rows:", fileMetadata.panel_table?.rows?.length)
```

- [ ] **Step 2: Verify the backend returns panel_table in parse response**

When the backend parses FCS files, it now returns `panel_table` with columns and fluorophore_labels. The frontend receives this and stores it as part of the file object. This should work automatically since the API response is JSON.

---

### Task 9: Tests

**Files:**
- Modify: `backend/tests/test_parser.py`
- Modify: `backend/tests/test_pdf.py`

- [ ] **Step 1: Add threshold parsing test**

In `test_parser.py`, add:

```python
def test_parse_fsc_threshold_bd_format():
    """BD-style: threshold: FSC,15000"""
    with patch('flowio.FlowData') as MockFlowData:
        mock_fd = MagicMock()
        mock_fd.text = {
            '$PAR': '1',
            '$P1N': 'FSC-A',
            'threshold': 'FSC,15000',
        }
        MockFlowData.return_value = mock_fd
        result = parse_fcs("dummy.fcs", "test.fcs")
        assert result.fsc_threshold == 15000.0

def test_parse_fsc_threshold_cytoflex_format():
    """CytoFLEX-style: ch1th=10000, ch1id=FSC"""
    with patch('flowio.FlowData') as MockFlowData:
        mock_fd = MagicMock()
        mock_fd.text = {
            '$PAR': '1',
            '$P1N': 'FSC-A',
            'ch1th': '10000',
            'ch1id': 'FSC',
        }
        MockFlowData.return_value = mock_fd
        result = parse_fcs("dummy.fcs", "test.fcs")
        assert result.fsc_threshold == 10000.0

def test_parse_no_threshold():
    """No threshold info in file"""
    with patch('flowio.FlowData') as MockFlowData:
        mock_fd = MagicMock()
        mock_fd.text = {'$PAR': '1', '$P1N': 'FSC-A'}
        MockFlowData.return_value = mock_fd
        result = parse_fcs("dummy.fcs", "test.fcs")
        assert result.fsc_threshold is None
```

- [ ] **Step 2: Add panel table parsing test**

```python
def test_parse_panel_table_from_spillover():
    """Panel table built from spillover fluorochrome list"""
    with patch('flowio.FlowData') as MockFlowData:
        mock_fd = MagicMock()
        mock_fd.text = {
            '$PAR': '3',
            '$P1N': 'FSC-A',
            '$P2N': 'FITC-A',
            '$P3N': 'PE-A',
            '$SPILLOVER': '2,FITC-A,PE-A,1.0,0.1,0.2,1.0',
        }
        MockFlowData.return_value = mock_fd
        result = parse_fcs("dummy.fcs", "test.fcs")
        assert result.panel_table is not None
        assert result.panel_table.columns == ['FL1', 'FL2']
        assert result.panel_table.fluorophore_labels == ['FITC', 'PE']
        assert result.panel_table.rows == []
```

- [ ] **Step 3: Add panel table PDF test**

In `test_pdf.py`, add a test that includes panel table data:

```python
def test_pdf_with_panel_table():
    """PDF generation with panel table data"""
    metadata = FCSMetadata(
        filename="test.fcs",
        timestamp="2023-01-01 12:00:00",
        instrument=InstrumentInfo(model="CytoFLEX"),
        channels=[ChannelInfo(name="FITC-A", voltage=100.0)],
        compensation=None,
        fsc_threshold=15000.0,
        panel_table=PanelTable(
            columns=["FL1", "FL2"],
            fluorophore_labels=["FITC", "PE"],
            rows=[
                ["1", "Sample-A", "CD4", "CD8"],
                ["2", "Sample-B", "CD45", "CD3"],
            ]
        )
    )
    
    pdf_bytes = generate_pdf_report(metadata)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF-")
```

---

### Task 10: Update API Tests

**Files:**
- Modify: `backend/tests/test_api.py`

- [ ] **Step 1: Update export test to include new fields**

```python
def test_export_pdf_with_panel_table():
    """Export PDF with panel table data via API"""
    mock_metadata = FCSMetadata(
        filename="test.fcs",
        instrument=InstrumentInfo(model="CytoFLEX"),
        channels=[ChannelInfo(name="FITC", voltage=500.0)],
        fsc_threshold=15000.0,
        panel_table=PanelTable(
            columns=["FL1"],
            fluorophore_labels=["FITC"],
            rows=[["1", "Control", "CD4", "test"]]
        )
    )
    
    response = client.post("/api/export/pdf", json=mock_metadata.model_dump())
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")
```

---

### Task 11: Final Verification

- [ ] **Step 1: Run all tests**

```bash
cd /home/user/PanChongshi/Repo/FASTVOLT
python -m pytest backend/tests/ -v
```

Expected: All tests pass.

- [ ] **Step 2: Start the application and test manually**

```bash
python main.py
```

Navigate to http://127.0.0.1:8000 and:
1. Upload an FCS file (from samples/)
2. Verify FSC Threshold appears in voltage table
3. Verify panel table is rendered with correct FL columns
4. Add rows, edit cells, delete rows
5. Export PDF and verify both threshold and panel table appear

- [ ] **Step 3: Commit all changes**

```bash
git add -A
git commit -m "feat: add FSC threshold display and editable panel table"
```
