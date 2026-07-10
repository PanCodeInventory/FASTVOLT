from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Table, TableStyle, Paragraph, Spacer, KeepTogether,
    PageBreak, NextPageTemplate,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import io
from ..models import FCSMetadata, PanelTable


def _register_cjk_font():
    """Register a CJK-capable font for the Experiment Name / Experimenter fields.

    Only those two user-editable fields use this — everything else keeps the
    original Helvetica look. We use ReportLab's built-in STSong-Light CID font,
    which needs no external files and works across environments. Falls back to
    Helvetica if even that is unavailable.
    """
    try:
        pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
        return 'STSong-Light'
    except Exception:
        return 'Helvetica'


# Resolved once at import time. Only experiment-info fields use this.
CJK_FONT = _register_cjk_font()

# --- Fixed font sizes (replaces the old "force onto one page" scaling) ---
# A4 content height (~27.7cm) holds all normal experiments; when a batch is
# very large the document simply flows onto more pages instead of being
# squeezed/clipped.
FONT_BODY = 9           # metadata / voltage table
FONT_COMP = 7           # compensation matrix (many columns)
FONT_PANEL = 8          # panel design table

# When a portrait compensation cell would be narrower than this, we rotate the
# matrix onto its own landscape page so long fluorochrome names get real room.
# 19cm portrait content / (n+1) cols < 2cm  ->  n >= 9
COMP_LANDSCAPE_MIN_CELL_CM = 2.0
COMP_LANDSCAPE_THRESHOLD = 9   # n fluorochromes at/above which we go landscape
# Panel table: rotate onto a landscape page when there are this many fluorochrome
# columns, so long labels (e.g. "PerCP-Cy5-5-A") get room instead of wrapping
# into very tall cells.
PANEL_LANDSCAPE_THRESHOLD = 6

# Page content boxes (A4 with 1cm margins on every side).
PORTRAIT_PAGE = A4
LANDSCAPE_PAGE = landscape(A4)
MARGIN = 1.0 * cm
PORTRAIT_CONTENT_W = PORTRAIT_PAGE[0] - 2 * MARGIN   # ~19cm
PORTRAIT_CONTENT_H = PORTRAIT_PAGE[1] - 2 * MARGIN
LANDSCAPE_CONTENT_W = LANDSCAPE_PAGE[0] - 2 * MARGIN  # ~27.7cm
LANDSCAPE_CONTENT_H = LANDSCAPE_PAGE[1] - 2 * MARGIN


def generate_pdf_report(metadata: FCSMetadata) -> bytes:
    """
    Generates a professional A4 PDF lab record for FCS data.

    Layout flows naturally across pages:
      - Header / instrument / voltage table stay together at the top.
      - The compensation matrix is wrapped in KeepTogether so it is never
        cut in the middle of a page.
      - Long fluorochrome names wrap inside their cells (Paragraph) instead
        of overflowing into neighbouring cells.
    """
    buffer = io.BytesIO()

    # 1. Setup Document — two page templates so the compensation matrix can
    #    be rotated onto a landscape page when there are many fluorochromes.
    doc = BaseDocTemplate(
        buffer,
        pagesize=PORTRAIT_PAGE,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
    )
    portrait_frame = Frame(MARGIN, MARGIN, PORTRAIT_CONTENT_W, PORTRAIT_CONTENT_H, id='portrait')
    landscape_frame = Frame(MARGIN, MARGIN, LANDSCAPE_CONTENT_W, LANDSCAPE_CONTENT_H, id='landscape')
    doc.addPageTemplates([
        PageTemplate(id='portrait', frames=[portrait_frame], pagesize=PORTRAIT_PAGE),
        PageTemplate(id='landscape', frames=[landscape_frame], pagesize=LANDSCAPE_PAGE),
    ])

    elements = []
    styles = getSampleStyleSheet()

    # Custom Styles
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        fontSize=14,
        spaceAfter=10
    )

    label_style = ParagraphStyle(
        'LabelStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=FONT_BODY,
        leading=FONT_BODY + 2
    )

    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=FONT_BODY + 1,
        spaceBefore=8,
        spaceAfter=5,
        textColor=colors.HexColor('#4a86e8')
    )

    # 2. Header: Institution Name
    elements.append(Paragraph("Institute of Immunology, USTC, Flow Cytometry Form", title_style))

    # 3. Experiment Information
    # Only this field uses the CJK-capable font (SimHei / "black body"), so users
    # can type Chinese experiment names / experimenter names without black squares.
    # Everything else in the document keeps the original Helvetica look.
    exp_info_style = ParagraphStyle(
        'ExpInfo',
        parent=label_style,
        fontName=CJK_FONT,   # supports CJK glyphs
    )
    exp_name = metadata.experiment_name.strip() if metadata.experiment_name else ""
    experimenter = metadata.experimenter.strip() if metadata.experimenter else ""
    exp_name_display = exp_name if exp_name else "____________________________"
    experimenter_display = experimenter if experimenter else "____________"
    exp_info_data = [
        [Paragraph(f"<b>Experiment Name:</b> {exp_name_display}", exp_info_style),
         Paragraph(f"<b>Experimenter:</b> {experimenter_display}", exp_info_style)]
    ]
    exp_table = Table(exp_info_data, colWidths=[11*cm, 8*cm])
    exp_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(exp_table)
    elements.append(Spacer(1, 5))

    # 4. FCS Metadata
    inst = metadata.instrument
    # Extract only the date part from timestamp (e.g. "19-Dec-2024 18:49:34" -> "19-Dec-2024")
    test_date = metadata.timestamp.split(' ')[0] if metadata.timestamp else "N/A"

    meta_data = [
        ["Instrument Model", f"{inst.model or 'N/A'} (SN: {inst.serial_number or 'N/A'})"],
        ["Test Date", test_date],
    ]

    meta_table = Table(meta_data, colWidths=[3.5*cm, 15.5*cm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), FONT_BODY - 1),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(meta_table)

    # 5. Voltage Table
    elements.append(Paragraph("Channel Voltages", section_title_style))

    vol_header = ["Channel", "Label", "Voltage"]
    vol_rows = [vol_header]
    for ch in metadata.channels:
        # Skip Time channels
        if ch.name and 'TIME' in ch.name.upper():
            continue
        vol_rows.append([ch.name, ch.label or "-", f"{ch.voltage:.2f}" if ch.voltage is not None else "N/A"])

    # Add FSC Threshold row if present
    has_threshold = metadata.fsc_threshold is not None
    if has_threshold:
        threshold_str = f"{metadata.fsc_threshold:,.0f}"
        vol_rows.append(["FSC Threshold", "-", threshold_str])

    vol_data_end = -2 if has_threshold else -1
    vol_table = Table(vol_rows, colWidths=[5*cm, 11*cm, 3*cm])
    vol_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4a86e8')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (2,0), (2,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), FONT_BODY),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0,1), (-1, vol_data_end), [colors.white, colors.whitesmoke]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    # Style the FSC Threshold row (last row) with green theme
    if has_threshold:
        last_row = len(vol_rows) - 1
        vol_table.setStyle(TableStyle([
            ('BACKGROUND', (0, last_row), (-1, last_row), colors.HexColor('#f0fdf4')),
            ('TEXTCOLOR', (0, last_row), (-1, last_row), colors.HexColor('#166534')),
            ('FONTNAME', (0, last_row), (-1, last_row), 'Helvetica-Bold'),
            ('LINEABOVE', (0, last_row), (-1, last_row), 1, colors.HexColor('#86efac')),
        ]))

    elements.append(vol_table)

    # 6 & 7. Compensation Matrix + Panel Design.
    # Both blocks can independently need a landscape page. To avoid emitting a
    # blank page when both are landscape (the old code restored portrait after
    # the matrix, then immediately switched back to landscape for the panel),
    # we decide the orientation for each block up front and switch templates
    # only when it actually changes.
    has_comp = metadata.compensation is not None
    has_panel = metadata.panel_table and metadata.panel_table.rows

    comp_landscape = has_comp and len(metadata.compensation.fluorochromes) >= COMP_LANDSCAPE_THRESHOLD
    panel_landscape = has_panel and len(metadata.panel_table.columns) >= PANEL_LANDSCAPE_THRESHOLD

    current_landscape = False   # document starts in portrait

    # --- Compensation Matrix ---
    if has_comp:
        if comp_landscape and not current_landscape:
            elements.append(NextPageTemplate('landscape'))
            elements.append(PageBreak())
            current_landscape = True
        elif not comp_landscape and current_landscape:
            elements.append(NextPageTemplate('portrait'))
            elements.append(PageBreak())
            current_landscape = False

        block = _build_compensation_block(
            metadata, section_title_style,
            LANDSCAPE_CONTENT_W if comp_landscape else PORTRAIT_CONTENT_W,
        )
        elements.append(KeepTogether(block))

    # --- Panel Design ---
    if has_panel:
        if panel_landscape and not current_landscape:
            # Coming from portrait: start a fresh landscape page.
            elements.append(NextPageTemplate('landscape'))
            elements.append(PageBreak())
            current_landscape = True
        elif panel_landscape and current_landscape:
            # Already landscape (compensation matrix above). If both tables share
            # one landscape page their combined height overflows and the bottom
            # gets clipped, so force a page break WITHIN landscape — same
            # orientation, just a fresh page. NextPageTemplate keeps us landscape.
            elements.append(NextPageTemplate('landscape'))
            elements.append(PageBreak())
        elif not panel_landscape and current_landscape:
            elements.append(NextPageTemplate('portrait'))
            elements.append(PageBreak())
            current_landscape = False

        if panel_landscape:
            # Title + table together; we just landed on a fresh landscape page.
            elements.append(Paragraph("Panel Design", section_title_style))
            elements.append(_build_panel_table(metadata.panel_table, LANDSCAPE_CONTENT_W))
        else:
            elements.append(KeepTogether([
                Paragraph("Panel Design", section_title_style),
                _build_panel_table(metadata.panel_table, PORTRAIT_CONTENT_W),
            ]))

    # Restore portrait for the footer if we ended in landscape.
    if current_landscape:
        elements.append(NextPageTemplate('portrait'))

    # 8. Footer
    elements.append(Spacer(1, 10))
    footer_text = "Generated by FASTVOLT, Software developed by Pan Chongshi"
    elements.append(Paragraph(f"<font color='grey' size='7'>{footer_text}</font>", styles['Normal']))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def _build_compensation_block(metadata: FCSMetadata, section_title_style, content_width: float) -> list:
    """Build the compensation matrix title + table as a flowable list.

    Cell labels are wrapped in Paragraph objects so that long fluorochrome
    names (e.g. 'PerCP-Cy5-5-A', 'APC-A700') wrap inside the cell width
    instead of overflowing into neighbouring cells.

    ``content_width`` is the usable page width (portrait or landscape) in
    reportlab points; cell widths are derived from it so the matrix fills
    whichever orientation it is rendered in.
    """
    block = [Paragraph("Compensation Matrix (%)", section_title_style)]

    comp = metadata.compensation
    row_labels = comp.fluorochromes
    col_labels = comp.fluorochromes

    n_cols = len(col_labels)
    cell_w = content_width / (n_cols + 1)

    # Paragraph styles sized to the cell width so wrapping kicks in correctly
    header_style = ParagraphStyle(
        'CompHeader',
        parent=section_title_style,
        fontName='Helvetica-Bold',
        fontSize=FONT_COMP,
        leading=FONT_COMP + 1,
        alignment=TA_CENTER,
        textColor=colors.whitesmoke,
        spaceBefore=0,
        spaceAfter=0,
    )
    row_label_style = ParagraphStyle(
        'CompRowLabel',
        parent=section_title_style,
        fontName='Helvetica',
        fontSize=FONT_COMP,
        leading=FONT_COMP + 1,
        alignment=TA_CENTER,
        textColor=colors.black,
        spaceBefore=0,
        spaceAfter=0,
    )

    # Header row: empty corner cell + wrapped column labels
    header_row = [Paragraph("", row_label_style)]
    for lbl in col_labels:
        header_row.append(Paragraph(str(lbl), header_style))

    comp_rows = [header_row]
    for i, row_vals in enumerate(comp.values):
        formatted_row = [Paragraph(str(row_labels[i]), row_label_style)]
        for v in row_vals:
            formatted_row.append("." if v == 0 else f"{(v*100):.2f}")
        comp_rows.append(formatted_row)

    comp_table = Table(comp_rows, colWidths=[cell_w]*(n_cols+1))
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
        ('BACKGROUND', (1,0), (-1,0), colors.HexColor('#4a86e8')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), FONT_COMP),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        # A little vertical breathing room so wrapped headers look balanced
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 1),
        ('RIGHTPADDING', (0,0), (-1,-1), 1),
    ]))
    block.append(comp_table)
    return block


def _build_panel_table(pt: PanelTable, content_width: float) -> Table:
    """Build the panel design table.

    Row layout in the data model:
        [Sample, FL1, FL2, ..., FLN, Comments]
    so the table renders N+2 columns: Sample | FL1..FLN | Comments.

    Cell content is wrapped in Paragraph objects so long fluorochrome names
    wrap inside the cell width instead of overflowing into neighbouring
    cells — mirroring how the compensation matrix is handled.

    ``content_width`` is the usable page width (portrait or landscape) in
    reportlab points; column widths are derived from it.
    """
    n_fl_cols = len(pt.columns)

    # Paragraph styles sized so wrapping kicks in correctly within each cell.
    header1_style = ParagraphStyle(
        'PanelH1',
        fontName='Helvetica-Bold',
        fontSize=FONT_PANEL,
        leading=FONT_PANEL + 1,
        alignment=TA_CENTER,
        textColor=colors.whitesmoke,
    )
    header2_style = ParagraphStyle(
        'PanelH2',
        fontName='Helvetica',
        fontSize=FONT_PANEL - 1,
        leading=FONT_PANEL,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#444444'),
    )
    cell_style = ParagraphStyle(
        'PanelCell',
        fontName='Helvetica',
        fontSize=FONT_PANEL,
        leading=FONT_PANEL + 1,
        alignment=TA_CENTER,
        textColor=colors.black,
    )

    def clean(s) -> str:
        """Stringify and strip newlines (from Word/Excel paste) to avoid black blocks."""
        s = str(s) if s is not None else ''
        return s.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')

    # Header row 1: Sample | FL1 | FL2 | ... | FLN | Comments
    h1 = [Paragraph("Sample", header1_style)]
    h1 += [Paragraph(clean(c), header1_style) for c in pt.columns]
    h1.append(Paragraph("Comments", header1_style))

    # Header row 2: "" | fluorophore labels | ""
    h2 = [Paragraph("", header2_style)]
    h2 += [Paragraph(clean(lbl), header2_style) for lbl in pt.fluorophore_labels]
    h2.append(Paragraph("", header2_style))

    table_data = [h1, h2]

    # Data rows - keep the full row: [Sample, FL1..FLN, Comments].
    for row in pt.rows:
        formatted = [Paragraph(clean(cell), cell_style) for cell in row]
        table_data.append(formatted)

    # Column widths derived from the usable page width.
    sample_w = 2.5 * cm
    comments_w = 3.0 * cm
    fl_available = content_width - sample_w - comments_w
    fl_each = max(1.2 * cm, fl_available / max(n_fl_cols, 1))
    col_widths = [sample_w] + [fl_each] * n_fl_cols + [comments_w]

    panel_table = Table(table_data, colWidths=col_widths, repeatRows=2)
    panel_table.setStyle(TableStyle([
        # Header row 1 styling
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4a86e8')),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        # Header row 2 styling
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#e8f0fe')),
        # Grid
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        # Row backgrounds for data
        ('ROWBACKGROUNDS', (0,2), (-1,-1), [colors.white, colors.whitesmoke]),
        # Padding
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    return panel_table
