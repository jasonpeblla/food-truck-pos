from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.database import get_db
from app.models import Payment, Order
from app.schemas import PaymentCreate, PaymentResponse

router = APIRouter(prefix="/payments", tags=["payments"])

@router.get("", response_model=List[PaymentResponse])
def get_payments(order_id: int = None, db: Session = Depends(get_db)):
    """Get payments, optionally filtered by order."""
    query = db.query(Payment)
    
    if order_id:
        query = query.filter(Payment.order_id == order_id)
    
    return query.order_by(Payment.created_at.desc()).all()

@router.post("", response_model=PaymentResponse)
def create_payment(payment_data: PaymentCreate, db: Session = Depends(get_db)):
    """Process a payment."""
    # Verify order exists
    order = db.query(Order).filter(Order.id == payment_data.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.is_paid:
        raise HTTPException(status_code=400, detail="Order is already paid")
    
    # Calculate change for cash payments
    change_given = 0.0
    total_with_tip = order.total + payment_data.tip
    
    if payment_data.method == "cash":
        if payment_data.cash_tendered:
            if payment_data.cash_tendered < total_with_tip:
                raise HTTPException(status_code=400, detail="Insufficient cash tendered")
            change_given = round(payment_data.cash_tendered - total_with_tip, 2)
    
    # Create payment
    payment = Payment(
        order_id=order.id,
        amount=payment_data.amount,
        method=payment_data.method,
        tip=payment_data.tip,
        change_given=change_given,
        reference=str(uuid.uuid4())[:8].upper()
    )
    db.add(payment)
    
    # Mark order as paid
    order.is_paid = True
    
    db.commit()
    db.refresh(payment)
    return payment

@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    """Get a specific payment."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment
