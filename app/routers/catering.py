from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Optional

from app.database import get_db, Base

router = APIRouter(prefix="/catering", tags=["catering"])

# Catering Order Model (create inline for simplicity)
class CateringOrder(Base):
    __tablename__ = "catering_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    customer_phone = Column(String, nullable=False)
    customer_email = Column(String, default="")
    event_name = Column(String, default="")
    event_date = Column(DateTime, nullable=False)
    event_location = Column(String, default="")
    guest_count = Column(Integer, default=10)
    
    # Order details (JSON-like text for simplicity)
    menu_items = Column(Text, default="")  # Comma-separated item descriptions
    special_requests = Column(Text, default="")
    
    # Pricing
    subtotal = Column(Float, default=0.0)
    service_fee = Column(Float, default=0.0)  # Usually 15-20% for catering
    deposit = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    deposit_paid = Column(Boolean, default=False)
    fully_paid = Column(Boolean, default=False)
    
    # Status
    status = Column(String, default="pending")  # pending, confirmed, preparing, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, default="")

# Pydantic models
class CateringItemRequest(BaseModel):
    name: str
    quantity: int
    price_per_unit: float

class CateringOrderCreate(BaseModel):
    customer_name: str
    customer_phone: str
    customer_email: str = ""
    event_name: str = ""
    event_date: str  # ISO format date
    event_location: str = ""
    guest_count: int = 10
    items: List[CateringItemRequest]
    special_requests: str = ""

class CateringOrderResponse(BaseModel):
    id: int
    customer_name: str
    customer_phone: str
    event_name: str
    event_date: datetime
    event_location: str
    guest_count: int
    menu_items: str
    special_requests: str
    subtotal: float
    service_fee: float
    deposit: float
    total: float
    deposit_paid: bool
    fully_paid: bool
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

SERVICE_FEE_RATE = 0.18  # 18% service fee for catering
DEPOSIT_RATE = 0.50  # 50% deposit required

@router.post("", response_model=CateringOrderResponse)
def create_catering_order(data: CateringOrderCreate, db: Session = Depends(get_db)):
    """Create a new catering order request."""
    # Parse event date
    try:
        event_dt = datetime.fromisoformat(data.event_date.replace('Z', '+00:00'))
    except:
        event_dt = datetime.strptime(data.event_date, "%Y-%m-%d")
    
    # Build menu items string and calculate subtotal
    items_str = []
    subtotal = 0.0
    for item in data.items:
        items_str.append(f"{item.quantity}x {item.name} @ ${item.price_per_unit:.2f}")
        subtotal += item.quantity * item.price_per_unit
    
    service_fee = round(subtotal * SERVICE_FEE_RATE, 2)
    total = round(subtotal + service_fee, 2)
    deposit = round(total * DEPOSIT_RATE, 2)
    
    order = CateringOrder(
        customer_name=data.customer_name,
        customer_phone=data.customer_phone,
        customer_email=data.customer_email,
        event_name=data.event_name,
        event_date=event_dt,
        event_location=data.event_location,
        guest_count=data.guest_count,
        menu_items="; ".join(items_str),
        special_requests=data.special_requests,
        subtotal=subtotal,
        service_fee=service_fee,
        deposit=deposit,
        total=total
    )
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return order

@router.get("", response_model=List[CateringOrderResponse])
def get_catering_orders(
    status: Optional[str] = None,
    upcoming_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get catering orders."""
    query = db.query(CateringOrder)
    
    if upcoming_only:
        query = query.filter(CateringOrder.event_date >= datetime.utcnow())
    
    if status:
        query = query.filter(CateringOrder.status == status)
    
    return query.order_by(CateringOrder.event_date).all()

@router.get("/{order_id}", response_model=CateringOrderResponse)
def get_catering_order(order_id: int, db: Session = Depends(get_db)):
    """Get a specific catering order."""
    order = db.query(CateringOrder).filter(CateringOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Catering order not found")
    return order

@router.patch("/{order_id}/status")
def update_catering_status(order_id: int, status: str, db: Session = Depends(get_db)):
    """Update catering order status."""
    order = db.query(CateringOrder).filter(CateringOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Catering order not found")
    
    valid = ["pending", "confirmed", "preparing", "completed", "cancelled"]
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid}")
    
    order.status = status
    db.commit()
    
    return {"status": status, "message": f"Order status updated to {status}"}

@router.post("/{order_id}/pay-deposit")
def pay_deposit(order_id: int, db: Session = Depends(get_db)):
    """Mark deposit as paid."""
    order = db.query(CateringOrder).filter(CateringOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Catering order not found")
    
    order.deposit_paid = True
    order.status = "confirmed"
    db.commit()
    
    return {"deposit_paid": True, "amount": order.deposit}

@router.post("/{order_id}/pay-full")
def pay_full(order_id: int, db: Session = Depends(get_db)):
    """Mark as fully paid."""
    order = db.query(CateringOrder).filter(CateringOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Catering order not found")
    
    order.deposit_paid = True
    order.fully_paid = True
    db.commit()
    
    return {"fully_paid": True, "total": order.total}

@router.get("/pricing/estimate")
def estimate_catering(guest_count: int = 10, per_person: float = 15.0):
    """Get a quick catering price estimate."""
    subtotal = guest_count * per_person
    service_fee = round(subtotal * SERVICE_FEE_RATE, 2)
    total = round(subtotal + service_fee, 2)
    deposit = round(total * DEPOSIT_RATE, 2)
    
    return {
        "guest_count": guest_count,
        "per_person": per_person,
        "subtotal": subtotal,
        "service_fee": service_fee,
        "service_fee_rate": f"{SERVICE_FEE_RATE * 100:.0f}%",
        "total": total,
        "deposit_required": deposit,
        "deposit_rate": f"{DEPOSIT_RATE * 100:.0f}%"
    }
