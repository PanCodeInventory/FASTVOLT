import pytest
from backend.app.services.pdf_renderer import generate_pdf_report
from backend.app.models import FCSMetadata, ChannelInfo, CompensationMatrix, InstrumentInfo

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
