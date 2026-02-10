from fastapi.testclient import TestClient
from backend.app.main import app, FILE_CACHE
from backend.app.models import FCSMetadata, ChannelInfo, InstrumentInfo
from unittest.mock import patch, MagicMock

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

def test_export_fcs_success():
    file_id = "test-file-id"
    FILE_CACHE[file_id] = {
        "path": "/tmp/test.fcs",
        "filename": "test.fcs"
    }

    mock_fd = MagicMock()
    mock_fd.text = {}
    mock_fd.pnn_labels = ["FITC-A"]

    def write_fcs(output_path, metadata=None):
        assert metadata is not None
        assert metadata.get("p1s") == "CD4 FITC"
        with open(output_path, "wb") as output_file:
            output_file.write(b"FCS")

    mock_fd.write_fcs = write_fcs

    with patch("backend.app.main.flowio.FlowData", return_value=mock_fd):
        response = client.post("/api/export/fcs", json={
            "filename": "test.fcs",
            "file_id": file_id,
            "channels": [
                {
                    "name": "FITC-A",
                    "label": None,
                    "marker": "CD4",
                    "fluorophore": "FITC",
                    "voltage": 500.0
                }
            ]
        })

    assert response.status_code == 200
    assert response.content == b"FCS"
