from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
from datetime import datetime
from ..models import FCSMetadata, PanelTable

def generate_pdf_report(metadata: FCSMetadata) -> bytes:
    """
    Generates a professional A4 PDF lab record for FCS data, scaled to fit on ONE page.
    """
    buffer = io.BytesIO()
    
    # 1. Setup Document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.0*cm,
        leftMargin=1.0*cm,
        topMargin=1.0*cm,
        bottomMargin=1.0*cm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # --- Dynamic Scaling Logic ---
    # We estimate height to decide on font sizes
    n_channels = len(metadata.channels)
    has_comp = metadata.compensation is not None
    n_comp = len(metadata.compensation.fluorochromes) if has_comp else 0
    
    # Base configuration
    base_font_size = 10
    base_row_h = 0.6 * cm
    
    # If we have a lot of data, shrink everything
    total_rows = n_channels + n_comp + 10 # 10 is buffer for headers/info
    
    if total_rows > 60:
        scale_factor = 0.6
    elif total_rows > 45:
        scale_factor = 0.75
    elif total_rows > 30:
        scale_factor = 0.85
    else:
        scale_factor = 1.0
        
    font_size = max(6, int(base_font_size * scale_factor))
    row_h = max(0.35*cm, base_row_h * scale_factor)
    
    # Custom Styles
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=14,
        spaceAfter=10
    )
    
    label_style = ParagraphStyle(
        'LabelStyle',
        parent=styles['Normal'],
        fontSize=font_size,
        leading=font_size + 2
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=font_size + 1,
        spaceBefore=8,
        spaceAfter=5,
        textColor=colors.HexColor('#4a86e8')
    )

    # 2. Header: Institution Name
    elements.append(Paragraph("Institute of Immunology, USTC, Flow Cytometry Form", title_style))
    
    # 3. Experiment Information
    exp_info_data = [
        [Paragraph("<b>Experiment Name:</b> ____________________________", label_style), 
         Paragraph("<b>Experimenter:</b> ____________", label_style)]
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
        ["Filename", metadata.filename]
    ]
    
    meta_table = Table(meta_data, colWidths=[3.5*cm, 15.5*cm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), font_size - 1),
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
        ('FONTSIZE', (0,0), (-1,-1), font_size),
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

    # 6. Compensation Matrix
    if has_comp:
        elements.append(Paragraph("Compensation Matrix (%)", section_title_style))
        
        comp = metadata.compensation
        row_labels = comp.fluorochromes
        col_labels = comp.fluorochromes
        
        comp_rows = [ [""] + col_labels ]
        for i, row_vals in enumerate(comp.values):
            formatted_row = [row_labels[i]]
            for v in row_vals:
                formatted_row.append("." if v == 0 else f"{(v*100):.2f}")
            comp_rows.append(formatted_row)
            
        n_cols = len(col_labels)
        # Extreme shrinking for matrix
        comp_font = max(5, font_size - 2)
        cell_w = 19 * cm / (n_cols + 1)
        
        comp_table = Table(comp_rows, colWidths=[cell_w]*(n_cols+1))
        comp_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
            ('BACKGROUND', (1,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTSIZE', (0,0), (-1,-1), comp_font),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(comp_table)

    # 7. Panel Table (Fluorophore-Sample Design)
    if metadata.panel_table and metadata.panel_table.rows:
        elements.append(Paragraph("Panel Design (Fluorophore-Sample)", section_title_style))
        
        pt = metadata.panel_table
        n_fl_cols = len(pt.columns)
        
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
        
        # Column widths: NO, Fluor, each FL, Comments
        total_col_width = 19 * cm
        fl_fixed = 1.2 * cm + 2.5 * cm + 2.0 * cm  # NO + Fluor + Comments
        fl_available = total_col_width - fl_fixed
        fl_each = max(1.2*cm, fl_available / max(n_fl_cols, 1))
        col_widths = [1.2*cm, 2.5*cm] + [fl_each] * n_fl_cols + [2.0*cm]
        
        panel_font = max(6, font_size - 1)
        
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
            # Row backgrounds for data
            ('ROWBACKGROUNDS', (0,2), (-1,-1), [colors.white, colors.whitesmoke]),
            # Padding
            ('LEFTPADDING', (0,0), (-1,-1), 3),
            ('RIGHTPADDING', (0,0), (-1,-1), 3),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))
        elements.append(panel_table)

    # 8. Footer
    elements.append(Spacer(1, 10))
    footer_text = f"Generated by FASTVOLT on {datetime.now().strftime('%Y-%m-%d')}"
    elements.append(Paragraph(f"<font color='grey' size='7'>{footer_text}</font>", styles['Normal']))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes