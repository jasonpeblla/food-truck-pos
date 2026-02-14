from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LocationCreate(BaseModel):
    name: str
    address: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: str = ""

class LocationUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None

class LocationResponse(BaseModel):
    id: int
    name: str
    address: str
    latitude: Optional[float]
    longitude: Optional[float]
    is_active: bool
    notes: str
    created_at: datetime
    
    class Config:
        from_attributes = True
