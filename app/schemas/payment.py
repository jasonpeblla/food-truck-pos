from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PaymentCreate(BaseModel):
    order_id: int
    amount: float
    method: str  # cash, card
    tip: float = 0.0
    cash_tendered: Optional[float] = None  # For cash payments

class PaymentResponse(BaseModel):
    id: int
    order_id: int
    amount: float
    method: str
    tip: float
    change_given: float
    reference: str
    created_at: datetime
    
    class Config:
        from_attributes = True
