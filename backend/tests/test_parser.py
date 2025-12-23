from backend.app.services.parser import parse_fcs
from backend.app.models import FCSMetadata
from unittest.mock import MagicMock, patch

def test_parse_fcs_success():
    # Mock flowio.FlowData
    with patch('flowio.FlowData') as MockFlowData:
        mock_fd = MagicMock()
        mock_fd.text = {
            '$PAR': '2',
            '$P1N': 'FITC-A',
            '$P1S': 'CD4',
            '$P1V': '450',
            '$P2N': 'PE-A',
            '$P2V': '500',
            '$SPILLOVER': '2,FITC-A,PE-A,1.0,0.1,0.2,1.0',
            '$DATE': '01-Jan-2023',
            '$BTIM': '12:00:00'
        }
        MockFlowData.return_value = mock_fd

        result = parse_fcs("dummy.fcs", "test_file.fcs")

        assert result.filename == "test_file.fcs"
        assert result.timestamp == "01-Jan-2023 12:00:00"
        assert len(result.channels) == 2
        assert result.channels[0].name == "FITC-A"
        assert result.channels[0].voltage == 450.0
        assert result.compensation is not None
        assert result.compensation.fluorochromes == ["FITC-A", "PE-A"]
        assert result.compensation.values == [[1.0, 0.1], [0.2, 1.0]]

def test_parse_instrument_info():
    with patch('flowio.FlowData') as MockFlowData:
        mock_fd = MagicMock()
        mock_fd.text = {
            '$PAR': '0', # No channels for this test
            '$MODEL': 'CytoFLEX LX',
            '$CYTSN': 'SN12345',
            '$CYT': 'MyCytometer'
        }
        MockFlowData.return_value = mock_fd

        result = parse_fcs("dummy.fcs", "test_file.fcs")
        
        assert result.instrument is not None
        assert result.instrument.model == 'CytoFLEX LX'
        assert result.instrument.serial_number == 'SN12345'
        assert result.instrument.name == 'MyCytometer'

def test_parse_fcs_error():
    with patch('flowio.FlowData', side_effect=Exception("File corrupted")):
        result = parse_fcs("bad.fcs", "bad.fcs")
        assert result.error == "File corrupted"
        assert len(result.channels) == 0
