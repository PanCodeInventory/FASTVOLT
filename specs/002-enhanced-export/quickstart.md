# Quickstart: Enhanced FCS Export

## New Dependencies

This feature introduces `reportlab` for PDF generation.

```bash
pip install reportlab
```

## How to use

1. **Upload FCS Files**: Use the drag-and-drop interface.
2. **Review Metadata**: The card will show extracted instrument info.
3. **Export PDF**:
   - Click the "Export PDF" button on a file card to get a single A4 lab record.
   - Click "Export All (PDF ZIP)" to download all reports in one archive.
4. **Manual Entry**: Print the PDF and fill in "Experiment Name" and "Experimenter" by hand on the provided lines.

## Testing

- **Layout Check**: Verify the header text "Institute of Immunology, USTC..." is correctly positioned.
- **Table Flow**: Test with a file containing >50 channels to ensure the table continues onto Page 2 correctly.
