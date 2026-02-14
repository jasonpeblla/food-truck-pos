from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date, timedelta

from app.database import get_db
from app.models import Order, Payment, OrderItem, MenuItem

router = APIRouter(prefix="/sales", tags=["sales"])

@router.get("/daily")
def get_daily_sales(target_date: str = None, db: Session = Depends(get_db)):
    """Get daily sales summary."""
    if target_date:
        try:
            report_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            report_date = date.today()
    else:
        report_date = date.today()
    
    # Get all completed orders for the date
    orders = db.query(Order).filter(
        func.date(Order.created_at) == report_date,
        Order.status.in_(["completed", "ready"])
    ).all()
    
    # Calculate totals
    total_orders = len(orders)
    total_revenue = sum(o.total for o in orders)
    total_tax = sum(o.tax for o in orders)
    paid_orders = len([o for o in orders if o.is_paid])
    
    # Get payments
    payments = db.query(Payment).filter(
        func.date(Payment.created_at) == report_date
    ).all()
    
    cash_total = sum(p.amount + p.tip for p in payments if p.method == "cash")
    card_total = sum(p.amount + p.tip for p in payments if p.method == "card")
    total_tips = sum(p.tip for p in payments)
    
    # Get item breakdown
    item_sales = db.query(
        MenuItem.name,
        func.sum(OrderItem.quantity).label("quantity"),
        func.sum(OrderItem.subtotal).label("revenue")
    ).join(OrderItem, OrderItem.menu_item_id == MenuItem.id
    ).join(Order, Order.id == OrderItem.order_id
    ).filter(
        func.date(Order.created_at) == report_date,
        Order.status.in_(["completed", "ready"])
    ).group_by(MenuItem.name).all()
    
    top_items = [
        {"name": name, "quantity": int(qty), "revenue": float(rev)}
        for name, qty, rev in item_sales
    ]
    top_items.sort(key=lambda x: x["quantity"], reverse=True)
    
    return {
        "date": report_date.isoformat(),
        "total_orders": total_orders,
        "paid_orders": paid_orders,
        "total_revenue": round(total_revenue, 2),
        "total_tax": round(total_tax, 2),
        "cash_total": round(cash_total, 2),
        "card_total": round(card_total, 2),
        "total_tips": round(total_tips, 2),
        "top_items": top_items[:10],
        "average_order_value": round(total_revenue / total_orders, 2) if total_orders > 0 else 0
    }

@router.get("/weekly")
def get_weekly_sales(db: Session = Depends(get_db)):
    """Get weekly sales summary."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    daily_totals = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        if day > today:
            break
            
        orders = db.query(Order).filter(
            func.date(Order.created_at) == day,
            Order.status.in_(["completed", "ready"])
        ).all()
        
        daily_totals.append({
            "date": day.isoformat(),
            "day_name": day.strftime("%A"),
            "orders": len(orders),
            "revenue": round(sum(o.total for o in orders), 2)
        })
    
    return {
        "week_start": week_start.isoformat(),
        "daily_totals": daily_totals,
        "total_orders": sum(d["orders"] for d in daily_totals),
        "total_revenue": round(sum(d["revenue"] for d in daily_totals), 2)
    }

@router.get("/hourly")
def get_hourly_breakdown(db: Session = Depends(get_db)):
    """Get hourly sales breakdown for today (useful for planning)."""
    today = date.today()
    
    hourly_data = []
    for hour in range(6, 22):  # 6 AM to 10 PM
        orders = db.query(Order).filter(
            func.date(Order.created_at) == today,
            func.extract('hour', Order.created_at) == hour,
            Order.status.in_(["completed", "ready"])
        ).all()
        
        hourly_data.append({
            "hour": hour,
            "time_label": f"{hour:02d}:00",
            "orders": len(orders),
            "revenue": round(sum(o.total for o in orders), 2)
        })
    
    return {
        "date": today.isoformat(),
        "hourly_data": hourly_data,
        "peak_hour": max(hourly_data, key=lambda x: x["orders"])["hour"] if hourly_data else None
    }
