from pydantic import BaseModel
from typing import List, Optional, Any

class InstrumentInfo(BaseModel):
    model: Optional[str] = None
    serial_number: Optional[str] = None
    name: Optional[str] = None

class ChannelInfo(BaseModel):
    name: str
    label: Optional[str] = None
    fluorophore: Optional[str] = None
    marker: Optional[str] = None
    voltage: Optional[float] = None

class CompensationMatrix(BaseModel):
    fluorochromes: List[str]
    values: List[List[float]]

class FCSMetadata(BaseModel):
    filename: str
    file_id: Optional[str] = None
    timestamp: Optional[str] = None
    instrument: Optional[InstrumentInfo] = None
    channels: List[ChannelInfo]
    compensation: Optional[CompensationMatrix] = None
    error: Optional[str] = None
