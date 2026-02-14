from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MenuItemCreate(BaseModel):
    name: str
    category: str
    price: float
    description: str = ""
    emoji: str = "🍽️"
    prep_time_seconds: int = 120
    display_order: int = 0

class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    is_available: Optional[bool] = None
    emoji: Optional[str] = None
    prep_time_seconds: Optional[int] = None
    display_order: Optional[int] = None

class MenuItemResponse(BaseModel):
    id: int
    name: str
    category: str
    price: float
    description: str
    is_available: bool
    emoji: str
    prep_time_seconds: int
    display_order: int
    created_at: datetime
    
    class Config:
        from_attributes = True
