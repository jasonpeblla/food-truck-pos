from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import Order, Payment

router = APIRouter(prefix="/refunds", tags=["refunds"])

class RefundRequest(BaseModel):
    order_id: int
    amount: Optional[float] = None  # None = full refund
    reason: str = ""

class RefundResponse(BaseModel):
    order_id: int
    original_amount: float
    refund_amount: float
    method: str
    reason: str
    refunded_at: datetime

@router.post("", response_model=RefundResponse)
def process_refund(refund: RefundRequest, db: Session = Depends(get_db)):
    """Process a refund for an order."""
    order = db.query(Order).filter(Order.id == refund.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if not order.is_paid:
        raise HTTPException(status_code=400, detail="Order has not been paid")
    
    payment = db.query(Payment).filter(Payment.order_id == order.id).first()
    if not payment:
        raise HTTPException(status_code=400, detail="No payment found for order")
    
    # Determine refund amount
    refund_amount = refund.amount if refund.amount else order.total
    
    if refund_amount > payment.amount:
        raise HTTPException(status_code=400, detail="Refund amount exceeds payment")
    
    # Mark order as refunded
    order.status = "refunded"
    order.notes = f"REFUNDED: {refund.reason}" if refund.reason else "REFUNDED"
    
    db.commit()
    
    return RefundResponse(
        order_id=order.id,
        original_amount=payment.amount,
        refund_amount=refund_amount,
        method=payment.method,
        reason=refund.reason,
        refunded_at=datetime.utcnow()
    )

@router.get("/history")
def get_refund_history(limit: int = 50, db: Session = Depends(get_db)):
    """Get history of refunded orders."""
    orders = db.query(Order).filter(
        Order.status == "refunded"
    ).order_by(Order.updated_at.desc()).limit(limit).all()
    
    results = []
    for order in orders:
        payment = db.query(Payment).filter(Payment.order_id == order.id).first()
        results.append({
            "order_id": order.id,
            "order_number": order.order_number,
            "customer_name": order.customer_name or "Guest",
            "amount": order.total,
            "payment_method": payment.method if payment else None,
            "reason": order.notes,
            "date": order.updated_at
        })
    
    return results
