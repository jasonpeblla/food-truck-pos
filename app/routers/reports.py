from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date, timedelta
from typing import Optional

from app.database import get_db
from app.models import Order, Payment, Shift

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/end-of-day")
def end_of_day_report(report_date: Optional[str] = None, db: Session = Depends(get_db)):
    """Generate comprehensive end-of-day report."""
    if report_date:
        target_date = datetime.strptime(report_date, "%Y-%m-%d").date()
    else:
        target_date = date.today()
    
    # Get all orders for the day
    orders = db.query(Order).filter(
        func.date(Order.created_at) == target_date
    ).all()
    
    total_orders = len(orders)
    completed_orders = len([o for o in orders if o.status == 'completed'])
    cancelled_orders = len([o for o in orders if o.status == 'cancelled'])
    
    # Revenue
    gross_revenue = sum(o.total for o in orders if o.is_paid)
    tax_collected = sum(o.tax for o in orders if o.is_paid)
    
    # Payments breakdown
    payments = db.query(Payment).filter(
        func.date(Payment.created_at) == target_date
    ).all()
    
    cash_total = sum(p.amount + (p.tip or 0) for p in payments if p.method == 'cash')
    card_total = sum(p.amount + (p.tip or 0) for p in payments if p.method == 'card')
    tips_total = sum(p.tip or 0 for p in payments)
    
    # Average order
    avg_order = gross_revenue / completed_orders if completed_orders > 0 else 0
    
    # Shift info
    shifts = db.query(Shift).filter(
        func.date(Shift.started_at) == target_date
    ).all()
    
    return {
        "date": str(target_date),
        "summary": {
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "cancelled_orders": cancelled_orders,
            "completion_rate": round(completed_orders / total_orders * 100, 1) if total_orders > 0 else 0
        },
        "revenue": {
            "gross_revenue": round(gross_revenue, 2),
            "tax_collected": round(tax_collected, 2),
            "net_revenue": round(gross_revenue - tax_collected, 2),
            "average_order_value": round(avg_order, 2)
        },
        "payments": {
            "cash_total": round(cash_total, 2),
            "card_total": round(card_total, 2),
            "tips_total": round(tips_total, 2),
            "total_collected": round(cash_total + card_total, 2)
        },
        "shifts": [
            {
                "staff": s.staff_name,
                "hours": round((s.ended_at - s.started_at).total_seconds() / 3600, 1) if s.ended_at else "active",
                "orders": s.total_orders,
                "cash_variance": s.cash_variance
            }
            for s in shifts
        ]
    }

@router.get("/weekly")
def weekly_report(db: Session = Depends(get_db)):
    """Get weekly performance summary."""
    today = date.today()
    week_ago = today - timedelta(days=7)
    
    orders = db.query(Order).filter(
        func.date(Order.created_at) >= week_ago,
        Order.is_paid == True
    ).all()
    
    # Daily breakdown
    daily_data = {}
    for order in orders:
        day = order.created_at.strftime("%Y-%m-%d")
        if day not in daily_data:
            daily_data[day] = {"orders": 0, "revenue": 0}
        daily_data[day]["orders"] += 1
        daily_data[day]["revenue"] += order.total
    
    total_revenue = sum(o.total for o in orders)
    total_orders = len(orders)
    
    return {
        "period": f"{week_ago} to {today}",
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "daily_average": round(total_revenue / 7, 2),
        "orders_per_day": round(total_orders / 7, 1),
        "daily_breakdown": daily_data,
        "best_day": max(daily_data.items(), key=lambda x: x[1]["revenue"])[0] if daily_data else None
    }

@router.get("/tax-summary")
def tax_summary(month: Optional[int] = None, year: Optional[int] = None, db: Session = Depends(get_db)):
    """Get tax summary for accounting."""
    if not month:
        month = date.today().month
    if not year:
        year = date.today().year
    
    from sqlalchemy import extract
    
    orders = db.query(Order).filter(
        extract('month', Order.created_at) == month,
        extract('year', Order.created_at) == year,
        Order.is_paid == True
    ).all()
    
    gross_sales = sum(o.total - o.tax for o in orders)
    tax_collected = sum(o.tax for o in orders)
    
    return {
        "period": f"{year}-{month:02d}",
        "gross_sales": round(gross_sales, 2),
        "tax_rate": "8.75%",
        "tax_collected": round(tax_collected, 2),
        "total_with_tax": round(gross_sales + tax_collected, 2),
        "order_count": len(orders)
    }
