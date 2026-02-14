from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date, timedelta

from app.database import get_db
from app.models import Payment, Shift

router = APIRouter(prefix="/tips", tags=["tips"])

@router.get("/today")
def get_today_tips(db: Session = Depends(get_db)):
    """Get today's tip summary."""
    today = date.today()
    
    payments = db.query(Payment).filter(
        func.date(Payment.created_at) == today
    ).all()
    
    total_tips = sum(p.tip or 0 for p in payments)
    cash_tips = sum(p.tip or 0 for p in payments if p.method == 'cash')
    card_tips = sum(p.tip or 0 for p in payments if p.method == 'card')
    tip_count = len([p for p in payments if p.tip and p.tip > 0])
    order_count = len(payments)
    
    avg_tip = total_tips / tip_count if tip_count > 0 else 0
    tip_rate = (tip_count / order_count * 100) if order_count > 0 else 0
    
    return {
        "date": str(today),
        "total_tips": round(total_tips, 2),
        "cash_tips": round(cash_tips, 2),
        "card_tips": round(card_tips, 2),
        "tip_count": tip_count,
        "order_count": order_count,
        "average_tip": round(avg_tip, 2),
        "tip_rate": round(tip_rate, 1)
    }

@router.get("/by-shift/{shift_id}")
def get_shift_tips(shift_id: int, db: Session = Depends(get_db)):
    """Get tips for a specific shift."""
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        return {"error": "Shift not found"}
    
    # Get payments during shift
    payments = db.query(Payment).filter(
        Payment.created_at >= shift.started_at,
        Payment.created_at <= (shift.ended_at or datetime.utcnow())
    ).all()
    
    total = sum(p.tip or 0 for p in payments)
    
    return {
        "shift_id": shift_id,
        "staff": shift.staff_name,
        "total_tips": round(total, 2),
        "orders": len(payments)
    }

@router.get("/weekly")
def get_weekly_tips(db: Session = Depends(get_db)):
    """Get weekly tip breakdown."""
    today = date.today()
    week_ago = today - timedelta(days=7)
    
    payments = db.query(Payment).filter(
        func.date(Payment.created_at) >= week_ago
    ).all()
    
    daily = {}
    for p in payments:
        day = p.created_at.strftime("%Y-%m-%d")
        if day not in daily:
            daily[day] = 0
        daily[day] += (p.tip or 0)
    
    total = sum(p.tip or 0 for p in payments)
    
    return {
        "period": f"{week_ago} to {today}",
        "total_tips": round(total, 2),
        "daily_breakdown": {k: round(v, 2) for k, v in daily.items()},
        "daily_average": round(total / 7, 2)
    }
