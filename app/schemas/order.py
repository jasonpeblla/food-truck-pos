from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int = 1
    customizations: str = ""

class OrderItemResponse(BaseModel):
    id: int
    menu_item_id: int
    menu_item_name: str
    quantity: int
    unit_price: float
    subtotal: float
    customizations: str
    
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    customer_name: str = ""
    items: List[OrderItemCreate]
    notes: str = ""
    location_id: Optional[int] = None

class OrderStatusUpdate(BaseModel):
    status: str  # pending, preparing, ready, completed, cancelled

class OrderResponse(BaseModel):
    id: int
    order_number: int
    customer_name: str
    status: str
    total: float
    tax: float
    notes: str
    is_paid: bool
    items: List[OrderItemResponse]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class QueueOrderResponse(BaseModel):
    order_number: int
    customer_name: str
    status: str
    items_summary: str
    wait_time_minutes: int
    
    class Config:
        from_attributes = True
