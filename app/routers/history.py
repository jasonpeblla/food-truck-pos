from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, date, timedelta
from pydantic import BaseModel

from app.database import get_db
from app.models import Order, OrderItem, MenuItem, Payment

router = APIRouter(prefix="/history", tags=["history"])

class OrderHistoryItem(BaseModel):
    id: int
    order_number: int
    customer_name: str
    status: str
    total: float
    is_paid: bool
    payment_method: Optional[str]
    item_count: int
    items_summary: str
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.get("/orders", response_model=List[OrderHistoryItem])
def get_order_history(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search customer name or order number"),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """Get order history with filters."""
    query = db.query(Order)
    
    # Date filters
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Order.created_at >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(Order.created_at < end)
        except ValueError:
            pass
    
    # Status filter
    if status:
        query = query.filter(Order.status == status)
    
    # Search filter
    if search:
        if search.isdigit():
            query = query.filter(Order.order_number == int(search))
        else:
            query = query.filter(Order.customer_name.ilike(f"%{search}%"))
    
    orders = query.order_by(Order.created_at.desc()).offset(offset).limit(limit).all()
    
    results = []
    for order in orders:
        # Get payment method
        payment = db.query(Payment).filter(Payment.order_id == order.id).first()
        
        # Build items summary
        items_summary = ", ".join([
            f"{oi.quantity}x {oi.menu_item.name}" for oi in order.items[:3]
        ])
        if len(order.items) > 3:
            items_summary += f" +{len(order.items) - 3} more"
        
        results.append({
            "id": order.id,
            "order_number": order.order_number,
            "customer_name": order.customer_name or "Guest",
            "status": order.status,
            "total": order.total,
            "is_paid": order.is_paid,
            "payment_method": payment.method if payment else None,
            "item_count": sum(oi.quantity for oi in order.items),
            "items_summary": items_summary,
            "created_at": order.created_at
        })
    
    return results

@router.get("/stats")
def get_stats(
    days: int = Query(7, description="Number of days to look back"),
    db: Session = Depends(get_db)
):
    """Get summary stats for recent period."""
    start_date = datetime.now() - timedelta(days=days)
    
    # Get orders in period
    orders = db.query(Order).filter(
        Order.created_at >= start_date,
        Order.status.in_(["completed", "ready"])
    ).all()
    
    payments = db.query(Payment).filter(
        Payment.created_at >= start_date
    ).all()
    
    # Calculate stats
    total_orders = len(orders)
    total_revenue = sum(o.total for o in orders)
    total_tips = sum(p.tip for p in payments)
    
    # Daily breakdown
    daily_stats = {}
    for order in orders:
        day = order.created_at.date().isoformat()
        if day not in daily_stats:
            daily_stats[day] = {"orders": 0, "revenue": 0}
        daily_stats[day]["orders"] += 1
        daily_stats[day]["revenue"] += order.total
    
    # Top items
    item_counts = {}
    for order in orders:
        for oi in order.items:
            name = oi.menu_item.name
            if name not in item_counts:
                item_counts[name] = {"quantity": 0, "revenue": 0}
            item_counts[name]["quantity"] += oi.quantity
            item_counts[name]["revenue"] += oi.subtotal
    
    top_items = sorted(item_counts.items(), key=lambda x: x[1]["quantity"], reverse=True)[:10]
    
    return {
        "period_days": days,
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "total_tips": round(total_tips, 2),
        "average_order_value": round(total_revenue / total_orders, 2) if total_orders > 0 else 0,
        "orders_per_day": round(total_orders / days, 1),
        "daily_breakdown": [
            {"date": day, **stats} for day, stats in sorted(daily_stats.items())
        ],
        "top_items": [
            {"name": name, **stats} for name, stats in top_items
        ]
    }

@router.get("/popular-times")
def get_popular_times(
    days: int = Query(7, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get popular ordering times."""
    start_date = datetime.now() - timedelta(days=days)
    
    orders = db.query(Order).filter(
        Order.created_at >= start_date,
        Order.status.in_(["completed", "ready"])
    ).all()
    
    # Hourly breakdown
    hourly = {h: 0 for h in range(24)}
    for order in orders:
        hour = order.created_at.hour
        hourly[hour] += 1
    
    # Day of week breakdown
    daily = {d: 0 for d in range(7)}
    for order in orders:
        day = order.created_at.weekday()
        daily[day] += 1
    
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    return {
        "period_days": days,
        "hourly_breakdown": [
            {"hour": h, "orders": count} for h, count in hourly.items()
        ],
        "daily_breakdown": [
            {"day": day_names[d], "orders": count} for d, count in daily.items()
        ],
        "peak_hour": max(hourly.items(), key=lambda x: x[1])[0] if orders else None,
        "peak_day": day_names[max(daily.items(), key=lambda x: x[1])[0]] if orders else None
    }
