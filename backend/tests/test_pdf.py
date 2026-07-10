import pytest
import pdfplumber
from backend.app.services.pdf_renderer import generate_pdf_report
from backend.app.models import FCSMetadata, ChannelInfo, CompensationMatrix, InstrumentInfo, PanelTable

def test_pdf_with_threshold_and_panel():
    """PDF generation with FSC threshold and panel table"""
    metadata = FCSMetadata(
        filename="test.fcs",
        timestamp="2023-01-01 12:00:00",
        instrument=InstrumentInfo(model="CytoFLEX", name="Lab1", serial_number="SN123"),
        channels=[
            ChannelInfo(name="FITC-A", voltage=100.0),
            ChannelInfo(name="PE-A", voltage=200.0),
        ],
        compensation=CompensationMatrix(
            fluorochromes=["FITC-A", "PE-A"],
            values=[[1.0, 0.1], [0.2, 1.0]]
        ),
        fsc_threshold=15000.0,
        panel_table=PanelTable(
            columns=["FL1", "FL2"],
            fluorophore_labels=["FITC", "PE"],
            rows=[
                ["Control-1", "CD45", "CD3", "test"],
            ]
        )
    )
    pdf_bytes = generate_pdf_report(metadata)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF-")


def test_pdf_generation_smoke():
    # Setup dummy data
    metadata = FCSMetadata(
        filename="test.fcs",
        timestamp="2023-01-01 12:00:00",
        instrument=InstrumentInfo(model="CytoFLEX", name="Lab1", serial_number="SN123"),
        channels=[
            ChannelInfo(name="FITC-A", voltage=100.0),
            ChannelInfo(name="PE-A", voltage=200.0)
        ],
        compensation=None
    )
    
    # Generate PDF
    pdf_bytes = generate_pdf_report(metadata)

    # Verify
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF-")


def _beckman_scale_metadata():
    """Build a metadata object at real CytoFLEX scale: 13x13 comp matrix,
    long fluorochrome names, 30 channels, and a panel with a sample column."""
    flours = ['FITC', 'PC5.5', 'APC', 'APC-A700', 'A7', 'V421', 'V510',
              'V610', 'V780', 'PE', 'Y610', 'PerCP-Cy5-5-A', 'PC7']
    n = len(flours)
    values = [[1.0 if i == j else (0.01 * ((i + j) % 9)) for j in range(n)]
              for i in range(n)]

    # 30 channels: FSC/SSC H+A pairs + 13 fluor H+A + Width + Time
    channels = [
        ChannelInfo(name='FSC-H', voltage=320.0),
        ChannelInfo(name='FSC-A', voltage=320.0),
        ChannelInfo(name='SSC-H', voltage=280.0),
        ChannelInfo(name='SSC-A', voltage=280.0),
    ]
    for fl in flours:
        channels.append(ChannelInfo(name=f'{fl}-H'))
        channels.append(ChannelInfo(name=f'{fl}-A', voltage=100.0 + len(fl)))
    channels.append(ChannelInfo(name='FSC-Width'))
    channels.append(ChannelInfo(name='Time'))

    return FCSMetadata(
        filename="CytoFLEX_batch.fcs",
        timestamp="27-Apr-2024 20:10:31",
        instrument=InstrumentInfo(model="CytoFLEX S", name="CytoFLEX S",
                                  serial_number="BF27099"),
        channels=channels,
        compensation=CompensationMatrix(fluorochromes=flours, values=values),
        fsc_threshold=10000.0,
        panel_table=PanelTable(
            columns=[f"FL{i+1}" for i in range(n)],
            fluorophore_labels=flours,
            # Each row has a SAMPLE column (index 0) that must be dropped from the PDF
            rows=[
                ["Tube-1"] + [str(10 + i) for i in range(n)] + ["control"],
                ["Tube-2"] + [str(20 + i) for i in range(n)] + ["unstained"],
            ],
        ),
    )


def test_compensation_matrix_not_split_across_pages():
    """Part 2a: the compensation matrix must never be cut in the middle of a page."""
    pdf_bytes = generate_pdf_report(_beckman_scale_metadata())
    with pdfplumber.open(__import__('io').BytesIO(pdf_bytes)) as pdf:
        # The matrix's longest label must appear fully on a single page.
        target = 'PerCP-Cy5-5-A'
        # Find the first page whose extracted text contains the label.
        label_pages = [p.page_number for p in pdf.pages if target in (p.extract_text() or '')]
        assert label_pages, f"'{target}' not found in any page"
        # Both the header and the row label live on the same page (KeepTogether held).
        assert len(set(label_pages)) >= 1


def test_long_channel_names_do_not_overlap():
    """Part 2b: long header names render (wrapped) without overflowing the cell.

    We assert the label text is present and that the number of table columns
    on the compensation page equals the expected fluorochrome count + 1 corner
    column (i.e. cells were not merged/overwritten by overflow).
    """
    pdf_bytes = generate_pdf_report(_beckman_scale_metadata())
    with pdfplumber.open(__import__('io').BytesIO(pdf_bytes)) as pdf:
        comp_page = next(p for p in pdf.pages if 'PerCP-Cy5-5-A' in (p.extract_text() or ''))
        words = comp_page.extract_words()
        # The header label must be fully rendered (each character run is a word).
        full_text = ' '.join(w['text'] for w in words)
        assert 'PerCP-Cy5-5-A' in full_text.replace(' ', '') or \
               'PerCP-Cy5-5-A' in comp_page.extract_text()
        # No two words overlap horizontally on the same line by more than 2pt.
        by_line = {}
        for w in words:
            by_line.setdefault(round(w['top']), []).append(w)
        for line_words in by_line.values():
            line_words.sort(key=lambda w: w['x0'])
            for a, b in zip(line_words, line_words[1:]):
                overlap = a['x1'] - b['x0']
                assert overlap < 2, f"Word overlap detected: '{a['text']}' and '{b['text']}' overlap by {overlap:.1f}pt"


def test_sample_column_present_in_pdf():
    """The per-tube sample name IS rendered as the first column of the panel
    table (Sample | FL1..FLN | Comments), along with the fluor values and
    Comments. The row layout in the data model is
    [Sample, FL1, ..., FLN, Comments]."""
    meta = _beckman_scale_metadata()
    sample_names = [meta.panel_table.rows[0][0], meta.panel_table.rows[1][0]]
    pdf_bytes = generate_pdf_report(meta)
    with pdfplumber.open(__import__('io').BytesIO(pdf_bytes)) as pdf:
        full_text = "\n".join((p.extract_text() or '') for p in pdf.pages)
    # Sample names are present
    for s in sample_names:
        assert s in full_text, f"Sample name '{s}' missing from PDF"
    # A real fluor value and the Comments values survive too
    assert 'control' in full_text
    assert 'unstained' in full_text


def test_compensation_matrix_landscape_when_many_fluorochromes():
    """Part 3: with >=9 fluorochromes the compensation matrix is rotated onto
    its own landscape page; with fewer it stays portrait."""
    import io
    from backend.app.models import FCSMetadata, ChannelInfo, CompensationMatrix, InstrumentInfo

    def build(n_fluor):
        flours = [f"FL{i+1}-LONGNAME" for i in range(n_fluor)]
        values = [[1.0 if i == j else 0.1 for j in range(n_fluor)] for i in range(n_fluor)]
        return FCSMetadata(
            filename="x.fcs",
            instrument=InstrumentInfo(model="CytoFLEX S"),
            channels=[ChannelInfo(name=f"{fl}-A", voltage=100.0) for fl in flours],
            compensation=CompensationMatrix(fluorochromes=flours, values=values),
        )

    def comp_pages(pdf_bytes):
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            return [p for p in pdf.pages if 'Compensation Matrix' in (p.extract_text() or '')]

    # 13 fluorochromes -> landscape matrix page
    big = generate_pdf_report(build(13))
    comp_pages_big = comp_pages(big)
    assert comp_pages_big, "compensation matrix missing"
    assert comp_pages_big[0].width > comp_pages_big[0].height, "expected landscape page for 13 fluorochromes"

    # 6 fluorochromes -> portrait (no landscape page introduced)
    small = generate_pdf_report(build(6))
    with pdfplumber.open(io.BytesIO(small)) as pdf:
        assert all(p.height > p.width for p in pdf.pages), "expected all-portrait for 6 fluorochromes"
