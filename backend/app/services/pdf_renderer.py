from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
import logging
from datetime import datetime
from ..models import FCSMetadata

logger = logging.getLogger(__name__)

def generate_pdf_report(metadata: FCSMetadata) -> bytes:
    """
    Generates a professional A4 PDF lab record for FCS data, scaled to fit on ONE page,
    or intelligently splits to two pages if content is too large.
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
    
    # Calculate available printable height
    printable_height = A4[1] - (doc.topMargin + doc.bottomMargin)
    
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
    
    # Relaxed scaling logic (T005) - rely on page break for very large datasets
    if total_rows > 50:
        scale_factor = 0.85
    elif total_rows > 35:
        scale_factor = 0.92
    else:
        scale_factor = 1.0
        
    font_size = max(8, int(base_font_size * scale_factor)) # Minimum 8pt
    row_h = max(0.45*cm, base_row_h * scale_factor)
    
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

    # --- Create Flowables (but don't add to elements yet) ---
    
    # 2. Header
    header_para = Paragraph("Institute of Immunology, USTC, Flow Cytometry Form", title_style)
    
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
    exp_spacer = Spacer(1, 5)

    # 4. FCS Metadata
    inst = metadata.instrument
    # Extract only the date part from timestamp
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

    # 5. Voltage Table
    voltage_title = Paragraph("Channel Voltages", section_title_style)
    
    vol_header = ["Channel", "Label", "Voltage"]
    vol_rows = [vol_header]
    for ch in metadata.channels:
        vol_rows.append([ch.name, ch.label or "-", f"{ch.voltage:.2f}" if ch.voltage is not None else "N/A"])
    
    vol_table = Table(vol_rows, colWidths=[5*cm, 11*cm, 3*cm])
    vol_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4a86e8')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (2,0), (2,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), font_size),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.whitesmoke]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    # --- Calculate Height of Content Above Matrix ---
    # We need to wrap them to know their height.
    # width is doc.width (which is pagesize - margins)
    avail_width = doc.width
    avail_height = doc.height # This is technically printable height too
    
    current_height = 0
    pre_matrix_elements = [header_para, exp_table, exp_spacer, meta_table, voltage_title, vol_table]
    
    for elem in pre_matrix_elements:
        w, h = elem.wrap(avail_width, avail_height)
        current_height += h
        
    # Add pre-matrix elements to story
    elements.extend(pre_matrix_elements)

    # 6. Compensation Matrix
    if has_comp:
        comp_title = Paragraph("Compensation Matrix (%)", section_title_style)
        
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
        
        # Calculate Matrix Height
        w_title, h_title = comp_title.wrap(avail_width, avail_height)
        w_table, h_table = comp_table.wrap(avail_width, avail_height)
        matrix_total_height = h_title + h_table
        
        # Conditional Logic (T006 & T008)
        if (current_height + matrix_total_height) > printable_height:
             # Page Split Triggered (T008)
             logger.info(f"Report content height ({current_height:.2f} + {matrix_total_height:.2f}) exceeds single A4 page ({printable_height:.2f}). Triggering page break for Compensation Matrix.")
             elements.append(PageBreak())
             elements.append(comp_title)
             elements.append(comp_table)
        else:
             # Fits on Page 1 (T006)
             logger.info(f"Report content fits on single A4 page. Height: {current_height + matrix_total_height:.2f} / {printable_height:.2f}")
             elements.append(comp_title)
             elements.append(comp_table)

    # 7. Footer
    elements.append(Spacer(1, 10))
    footer_text = f"Generated by FASTVOLT on {datetime.now().strftime('%Y-%m-%d')}"
    elements.append(Paragraph(f"<font color='grey' size='7'>{footer_text}</font>", styles['Normal']))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes