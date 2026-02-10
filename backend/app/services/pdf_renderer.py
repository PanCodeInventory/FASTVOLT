from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
from datetime import datetime
from ..models import FCSMetadata
import re

def normalize_channel_name(name: str) -> str:
    if not name:
        return ""
    return name.replace("-A", "").replace("-H", "")

def strip_fluor_from_label(label: str, fluor: str) -> str:
    if not label:
        return ""
    if not fluor:
        return label
    cleaned = re.sub(rf"\b{re.escape(fluor)}\b", "", label, flags=re.IGNORECASE)
    return " ".join(cleaned.split())

def extract_fluor_from_label(label: str) -> str:
    if not label:
        return ""
    tokens = [
        "FITC",
        "PE",
        "APC",
        "PERCP",
        "PERCP-CY5.5",
        "PE-CY7",
        "APC-CY7",
        "BV421",
        "BV510",
        "BV605",
        "BV650",
        "BV711",
        "BV786",
        "AF488",
        "AF594",
        "AF647",
    ]
    upper = label.upper()
    for token in tokens:
        if token in upper:
            return token
    return ""

def generate_pdf_report(metadata: FCSMetadata) -> bytes:
    """
    Generates a professional A4 PDF lab record for FCS data, scaled to fit on ONE page.
    """
    buffer = io.BytesIO()
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

    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=13,
        spaceAfter=6
    )

    label_style = ParagraphStyle(
        'LabelStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=11
    )

    elements.append(Paragraph("Institute of Immunology, USTC, Flow Cytometry Form", title_style))

    fl_labels = [f"FL{i}" for i in range(1, 11)]
    comp = metadata.compensation

    raw_fluorescence = [
        ch for ch in metadata.channels
        if "FSC" not in ch.name.upper() and "SSC" not in ch.name.upper() and "TIME" not in ch.name.upper()
    ]
    fluorescence_channels = []
    seen = set()
    for ch in raw_fluorescence:
        base = normalize_channel_name(ch.name)
        if base and base not in seen:
            seen.add(base)
            fluorescence_channels.append(ch)

    comp_index = {}
    if comp:
        for fl_idx, ch in enumerate(fluorescence_channels[:10]):
            ch_name = normalize_channel_name(ch.name).upper()
            found = None
            for idx, name in enumerate(comp.fluorochromes):
                comp_name = normalize_channel_name(name).upper()
                if comp_name == ch_name or comp_name in ch_name or ch_name in comp_name:
                    found = idx
                    break
            if found is not None:
                comp_index[fl_idx] = found

    comp_rows = [["COMPENSATION Y~X"] + [""] * 10]
    comp_rows.append([""] + fl_labels)
    for i in range(10):
        row = [fl_labels[i]]
        for j in range(10):
            value = ""
            if comp and i in comp_index and j in comp_index:
                raw = comp.values[comp_index[i]][comp_index[j]]
                if raw is not None:
                    value = "0" if raw == 0 else f"{raw:.3f}"
            row.append(value)
        comp_rows.append(row)

    comp_table = Table(comp_rows, colWidths=[1.2*cm] + [1.3*cm]*10)
    comp_table.setStyle(TableStyle([
        ('SPAN', (0,0), (-1,0)),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
    ]))

    signal_rows = [["SIGNAL", "VOLTS"]]
    signal_names = ["FSC", "SSC"] + fl_labels
    voltage_map = {}
    for idx, ch in enumerate(fluorescence_channels[:10], start=1):
        voltage_map[f"FL{idx}"] = ch.voltage

    for signal in signal_names:
        if signal in ["FSC", "SSC"]:
            match = next((ch for ch in metadata.channels if signal in ch.name.upper()), None)
            volts = match.voltage if match else None
        else:
            volts = voltage_map.get(signal)
        signal_rows.append([signal, "" if volts is None else f"{volts:.2f}"])

    signal_table = Table(signal_rows, colWidths=[2*cm, 2*cm])
    signal_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
    ]))

    comp_block = Table([[comp_table, signal_table]], colWidths=[15.5*cm, 3.5*cm])
    comp_block.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (0,0), 0.5, colors.black),
    ]))

    elements.append(comp_block)
    elements.append(Spacer(1, 4))

    threshold_table = Table([
        ["THRESHOLD", "FSC", "________"],
    ], colWidths=[3*cm, 3*cm, 13*cm])
    threshold_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ]))
    elements.append(threshold_table)
    elements.append(Spacer(1, 6))

    info_rows = [
        [Paragraph("<b>Experiment#</b> ____________________________", label_style), Paragraph("<b>Operator:</b> ____________", label_style)],
        [Paragraph("<b>Experiment:</b> Date ________  Initiation time ________  Completion time ________", label_style), ""],
        [Paragraph("<b>Flow Cytometry:</b> Date ________  Initiation time ________  Completion time ________", label_style), ""],
    ]
    info_table = Table(info_rows, colWidths=[12.5*cm, 6.5*cm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6))

    fluor_names = ["" for _ in range(10)]
    for idx, ch in enumerate(fluorescence_channels[:10], start=1):
        fluor_names[idx - 1] = normalize_channel_name(ch.name)

    header_row = ["NO.", "SIGNAL"] + fl_labels + ["Comments"]
    fluor_row = ["", "Fluor."] + fluor_names + [""]
    table_rows = [header_row, fluor_row]

    sample_name = metadata.filename.replace('.fcs', '').replace('.FCS', '')
    label_row = ["1", sample_name]
    for idx in range(10):
        label_value = ""
        if idx < len(fluorescence_channels):
            fluor = normalize_channel_name(fluorescence_channels[idx].name)
            label_value = strip_fluor_from_label(fluorescence_channels[idx].label or "", fluor)
        label_row.append(label_value)
    label_row.append("")
    table_rows.append(label_row)

    for i in range(2, 25):
        table_rows.append([str(i), ""] + [""] * 10 + [""])

    main_table = Table(table_rows, colWidths=[0.8*cm, 2.5*cm] + [1.2*cm]*10 + [2.5*cm])
    main_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,1), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(main_table)
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("FACS Form-2 Keep in Lab book", label_style))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

def generate_panel_summary_pdf(panel_name: str, samples: list, channel_map_default: dict, compensation: dict | None) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.0*cm,
        leftMargin=1.0*cm,
        topMargin=1.0*cm,
        bottomMargin=1.0*cm
    )

    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle(
        'PanelTitle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=14,
        spaceAfter=10
    )

    label_style = ParagraphStyle(
        'PanelLabel',
        parent=styles['Normal'],
        fontSize=9,
        leading=11
    )

    elements.append(Paragraph(f"Institute of Immunology, USTC, Flow Cytometry Form", title_style))

    fl_labels = [f"FL{i}" for i in range(1, 11)]
    comp_fluorochromes = compensation.get("fluorochromes", []) if compensation else []
    comp_values = compensation.get("values", []) if compensation else []

    first_sample = samples[0] if samples else {}
    raw_fluorescence = [
        ch for ch in first_sample.get("channels", [])
        if "FSC" not in ch.get("name", "").upper() and "SSC" not in ch.get("name", "").upper() and "TIME" not in ch.get("name", "").upper()
    ]
    fluorescence_channels = []
    seen = set()
    for ch in raw_fluorescence:
        base = normalize_channel_name(ch.get("name", ""))
        if base and base not in seen:
            seen.add(base)
            fluorescence_channels.append(ch)

    comp_index = {}
    if comp_fluorochromes:
        for fl_idx, ch in enumerate(fluorescence_channels[:10]):
            ch_name = normalize_channel_name(ch.get("name", "")).upper()
            found = None
            for idx, name in enumerate(comp_fluorochromes):
                comp_name = normalize_channel_name(name).upper()
                if comp_name == ch_name or comp_name in ch_name or ch_name in comp_name:
                    found = idx
                    break
            if found is not None:
                comp_index[fl_idx] = found

    comp_rows = [["COMPENSATION Y~X"] + [""] * 10]
    comp_rows.append([""] + fl_labels)
    for i in range(10):
        row = [fl_labels[i]]
        for j in range(10):
            value = ""
            if comp_values and i in comp_index and j in comp_index:
                raw = comp_values[comp_index[i]][comp_index[j]]
                if raw is not None:
                    value = "0" if raw == 0 else f"{raw:.3f}"
            row.append(value)
        comp_rows.append(row)

    comp_table = Table(comp_rows, colWidths=[1.2*cm] + [1.3*cm]*10)
    comp_table.setStyle(TableStyle([
        ('SPAN', (0,0), (-1,0)),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
    ]))

    signal_rows = [["SIGNAL", "VOLTS"]]
    signal_names = ["FSC", "SSC"] + fl_labels
    voltage_map = {}
    for idx, ch in enumerate(fluorescence_channels[:10], start=1):
        voltage_map[f"FL{idx}"] = ch.get("voltage")

    for signal in signal_names:
        if signal in ["FSC", "SSC"]:
            match = next((ch for ch in first_sample.get("channels", []) if signal in ch.get("name", "").upper()), None)
            volts = match.get("voltage") if match else None
        else:
            volts = voltage_map.get(signal)
        signal_rows.append([signal, "" if volts is None else f"{volts:.2f}"])

    signal_table = Table(signal_rows, colWidths=[2*cm, 2*cm])
    signal_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
    ]))

    comp_block = Table([[comp_table, signal_table]], colWidths=[15.5*cm, 3.5*cm])
    comp_block.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (0,0), 0.5, colors.black),
    ]))
    elements.append(comp_block)
    elements.append(Spacer(1, 4))

    threshold_table = Table([
        ["THRESHOLD", "FSC", "________"],
    ], colWidths=[3*cm, 3*cm, 13*cm])
    threshold_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ]))
    elements.append(threshold_table)
    elements.append(Spacer(1, 6))

    info_rows = [
        [Paragraph("<b>Experiment#</b> ____________________________", label_style), Paragraph("<b>Operator:</b> ____________", label_style)],
        [Paragraph("<b>Experiment:</b> Date ________  Initiation time ________  Completion time ________", label_style), ""],
        [Paragraph("<b>Flow Cytometry:</b> Date ________  Initiation time ________  Completion time ________", label_style), ""],
    ]
    info_table = Table(info_rows, colWidths=[12.5*cm, 6.5*cm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6))

    def panel_default_label(base_name: str) -> str:
        entry = channel_map_default.get(base_name, {})
        return entry.get("label", "") if entry else ""

    def sample_channel_label(sample, base_name: str) -> str:
        for ch in sample.get("channels", []):
            if normalize_channel_name(ch.get("name", "")) == base_name:
                return ch.get("label", "") or ""
        return ""

    fluor_names = ["" for _ in range(10)]
    for idx, ch in enumerate(fluorescence_channels[:10], start=1):
        base_name = normalize_channel_name(ch.get("name", ""))
        default_label = panel_default_label(base_name)
        sample_label = sample_channel_label(first_sample, base_name)
        fluor = extract_fluor_from_label(default_label) or extract_fluor_from_label(sample_label)
        fluor_names[idx - 1] = fluor or base_name

    header_row = ["NO.", "SIGNAL"] + fl_labels + ["Comments"]
    fluor_row = ["", "Fluor."] + fluor_names + [""]
    table_rows = [header_row, fluor_row]

    def label_for_sample(sample, base_name, fluor):
        default_entry = channel_map_default.get(base_name, {})
        default_label = default_entry.get("label", "") if default_entry else ""
        label_value = default_label
        for ch in sample.get("channels", []):
            if normalize_channel_name(ch.get("name", "")) == base_name:
                label_value = label_value or ch.get("label") or ""
                break
        return strip_fluor_from_label(label_value, fluor)

    for idx, sample in enumerate(samples, start=1):
        row = [str(idx), sample.get("filename", "")]
        for fl_idx in range(10):
            base_name = normalize_channel_name(fluorescence_channels[fl_idx].get("name", "")) if fl_idx < len(fluorescence_channels) else ""
            fluor = fluor_names[fl_idx] if fl_idx < len(fluor_names) else ""
            row.append(label_for_sample(sample, base_name, fluor) if base_name else "")
        row.append("")
        table_rows.append(row)

    for i in range(len(samples) + 1, 25):
        table_rows.append([str(i), ""] + [""] * 10 + [""])

    main_table = Table(table_rows, colWidths=[0.8*cm, 2.5*cm] + [1.2*cm]*10 + [2.5*cm])
    main_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,1), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(main_table)
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("FACS Form-2 Keep in Lab book", label_style))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
