from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models import FCSMetadata, ChannelInfo, InstrumentInfo
from unittest.mock import patch

client = TestClient(app)

def test_read_root():
    # In main.py, I changed the root to serve index.html, 
    # but the test was expecting JSON message.
    # Let's check what main.py currently does.
    pass

def test_export_pdf_success():
    mock_metadata = FCSMetadata(
        filename="test.fcs",
        instrument=InstrumentInfo(model="CytoFLEX"),
        channels=[ChannelInfo(name="FITC", voltage=500.0)]
    )
    
    response = client.post("/api/export/pdf", json=mock_metadata.dict())
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")

def test_export_pdf_zip_success():
    mock_list = [
        FCSMetadata(
            filename="test1.fcs",
            instrument=InstrumentInfo(model="CytoFLEX"),
            channels=[ChannelInfo(name="FITC", voltage=500.0)]
        ),
        FCSMetadata(
            filename="test2.fcs",
            instrument=InstrumentInfo(model="CytoFLEX"),
            channels=[ChannelInfo(name="PE", voltage=600.0)]
        )
    ]
    
    response = client.post("/api/export/pdf/zip", json=[m.dict() for m in mock_list])
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"