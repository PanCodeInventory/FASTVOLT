from pydantic import BaseModel
from typing import List, Optional, Any

class InstrumentInfo(BaseModel):
    model: Optional[str] = None
    serial_number: Optional[str] = None
    name: Optional[str] = None

class ChannelInfo(BaseModel):
    name: str
    label: Optional[str] = None
    voltage: Optional[float] = None

class CompensationMatrix(BaseModel):
    fluorochromes: List[str]
    values: List[List[float]]

class PanelTable(BaseModel):
    """Editable fluorophore-sample panel design table."""
    columns: List[str]                     # ["FL1", "FL2", ..., "FLN"]
    fluorophore_labels: List[Optional[str]]  # ["FITC", "PE", ..., None]
    rows: List[List[Optional[str]]]          # Each row: [NO, Fluor, FL1_val, ..., FLN_val, Comments]

class FCSMetadata(BaseModel):
    filename: str
    timestamp: Optional[str] = None
    instrument: Optional[InstrumentInfo] = None
    channels: List[ChannelInfo]
    compensation: Optional[CompensationMatrix] = None
    fsc_threshold: Optional[float] = None
    panel_table: Optional[PanelTable] = None
    experiment_name: Optional[str] = None
    experimenter: Optional[str] = None
    error: Optional[str] = None
