from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.shift import Shift
from app.models import Order, Payment

router = APIRouter(prefix="/shifts", tags=["shifts"])

# Schemas
class ShiftStart(BaseModel):
    staff_name: str
    starting_cash: float = 0.0

class ShiftClose(BaseModel):
    ending_cash: float
    notes: str = ""

class ShiftResponse(BaseModel):
    id: int
    staff_name: str
    started_at: datetime
    ended_at: Optional[datetime]
    is_active: bool
    starting_cash: float
    ending_cash: Optional[float]
    expected_cash: Optional[float]
    total_orders: int
    total_revenue: float
    total_tips: float
    cash_sales: float
    card_sales: float
    cash_variance: Optional[float] = None
    
    class Config:
        from_attributes = True

@router.get("/active", response_model=Optional[ShiftResponse])
def get_active_shift(db: Session = Depends(get_db)):
    """Get the currently active shift."""
    shift = db.query(Shift).filter(Shift.is_active == True).first()
    if shift and shift.ending_cash is not None:
        return {**shift.__dict__, "cash_variance": shift.ending_cash - (shift.expected_cash or 0)}
    return shift

@router.get("", response_model=List[ShiftResponse])
def get_shifts(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent shifts."""
    shifts = db.query(Shift).order_by(Shift.started_at.desc()).limit(limit).all()
    results = []
    for shift in shifts:
        data = shift.__dict__.copy()
        if shift.ending_cash is not None and shift.expected_cash is not None:
            data["cash_variance"] = shift.ending_cash - shift.expected_cash
        results.append(data)
    return results

@router.post("/start", response_model=ShiftResponse)
def start_shift(shift_data: ShiftStart, db: Session = Depends(get_db)):
    """Start a new shift."""
    # Check for existing active shift
    existing = db.query(Shift).filter(Shift.is_active == True).first()
    if existing:
        raise HTTPException(status_code=400, detail="There is already an active shift. Close it first.")
    
    shift = Shift(
        staff_name=shift_data.staff_name,
        starting_cash=shift_data.starting_cash
    )
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift

@router.post("/close", response_model=ShiftResponse)
def close_shift(close_data: ShiftClose, db: Session = Depends(get_db)):
    """Close the active shift."""
    shift = db.query(Shift).filter(Shift.is_active == True).first()
    if not shift:
        raise HTTPException(status_code=404, detail="No active shift to close")
    
    # Calculate shift totals
    orders = db.query(Order).filter(
        Order.created_at >= shift.started_at,
        Order.status.in_(["completed", "ready"]),
        Order.is_paid == True
    ).all()
    
    payments = db.query(Payment).filter(
        Payment.created_at >= shift.started_at
    ).all()
    
    shift.total_orders = len(orders)
    shift.total_revenue = sum(o.total for o in orders)
    shift.total_tips = sum(p.tip for p in payments)
    shift.cash_sales = sum(p.amount + p.tip for p in payments if p.method == "cash")
    shift.card_sales = sum(p.amount + p.tip for p in payments if p.method == "card")
    
    # Expected cash = starting + cash sales
    shift.expected_cash = shift.starting_cash + shift.cash_sales
    
    shift.ending_cash = close_data.ending_cash
    shift.notes = close_data.notes
    shift.ended_at = datetime.utcnow()
    shift.is_active = False
    
    db.commit()
    db.refresh(shift)
    
    return {
        **shift.__dict__,
        "cash_variance": shift.ending_cash - shift.expected_cash
    }

@router.get("/{shift_id}", response_model=ShiftResponse)
def get_shift(shift_id: int, db: Session = Depends(get_db)):
    """Get a specific shift."""
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    
    data = shift.__dict__.copy()
    if shift.ending_cash is not None and shift.expected_cash is not None:
        data["cash_variance"] = shift.ending_cash - shift.expected_cash
    return data
