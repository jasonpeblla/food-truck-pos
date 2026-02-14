from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class IngredientCreate(BaseModel):
    name: str
    unit: str = "units"
    stock_quantity: float = 0.0
    low_stock_threshold: float = 10.0
    cost_per_unit: float = 0.0

class IngredientUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    stock_quantity: Optional[float] = None
    low_stock_threshold: Optional[float] = None
    cost_per_unit: Optional[float] = None

class IngredientResponse(BaseModel):
    id: int
    name: str
    unit: str
    stock_quantity: float
    low_stock_threshold: float
    cost_per_unit: float
    is_low_stock: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True
