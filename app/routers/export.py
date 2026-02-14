from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import csv
import io

from app.database import get_db
from app.models import Order, Payment, MenuItem

router = APIRouter(prefix="/export", tags=["export"])

@router.get("/orders/csv")
def export_orders_csv(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Export orders to CSV."""
    query = db.query(Order)
    
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
    
    orders = query.order_by(Order.created_at.desc()).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Order Number", "Date", "Time", "Customer", "Items",
        "Subtotal", "Tax", "Total", "Status", "Paid", "Payment Method"
    ])
    
    for order in orders:
        payment = db.query(Payment).filter(Payment.order_id == order.id).first()
        items = ", ".join([f"{oi.quantity}x {oi.menu_item.name}" for oi in order.items])
        
        writer.writerow([
            order.order_number,
            order.created_at.strftime("%Y-%m-%d"),
            order.created_at.strftime("%H:%M:%S"),
            order.customer_name or "Guest",
            items,
            f"{order.total - order.tax:.2f}",
            f"{order.tax:.2f}",
            f"{order.total:.2f}",
            order.status,
            "Yes" if order.is_paid else "No",
            payment.method if payment else ""
        ])
    
    output.seek(0)
    
    filename = f"orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/sales/csv")
def export_sales_csv(
    days: int = Query(30),
    db: Session = Depends(get_db)
):
    """Export daily sales to CSV."""
    start_date = datetime.now() - timedelta(days=days)
    
    orders = db.query(Order).filter(
        Order.created_at >= start_date,
        Order.status.in_(["completed", "ready"])
    ).all()
    
    # Group by date
    daily_data = {}
    for order in orders:
        date_key = order.created_at.date()
        if date_key not in daily_data:
            daily_data[date_key] = {"orders": 0, "revenue": 0, "tax": 0}
        daily_data[date_key]["orders"] += 1
        daily_data[date_key]["revenue"] += order.total
        daily_data[date_key]["tax"] += order.tax
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Orders", "Revenue", "Tax"])
    
    for date_key in sorted(daily_data.keys()):
        data = daily_data[date_key]
        writer.writerow([
            date_key.isoformat(),
            data["orders"],
            f"{data['revenue']:.2f}",
            f"{data['tax']:.2f}"
        ])
    
    output.seek(0)
    
    filename = f"sales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/menu/csv")
def export_menu_csv(db: Session = Depends(get_db)):
    """Export menu to CSV."""
    items = db.query(MenuItem).order_by(MenuItem.category, MenuItem.display_order).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Name", "Category", "Price", "Description", "Emoji", 
        "Available", "Prep Time (sec)", "Display Order"
    ])
    
    for item in items:
        writer.writerow([
            item.name,
            item.category,
            f"{item.price:.2f}",
            item.description,
            item.emoji,
            "Yes" if item.is_available else "No",
            item.prep_time_seconds,
            item.display_order
        ])
    
    output.seek(0)
    
    filename = f"menu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/json")
def export_all_json(db: Session = Depends(get_db)):
    """Export all data as JSON."""
    menu = db.query(MenuItem).all()
    
    return {
        "exported_at": datetime.now().isoformat(),
        "menu": [
            {
                "name": item.name,
                "category": item.category,
                "price": item.price,
                "description": item.description,
                "emoji": item.emoji,
                "is_available": item.is_available,
                "prep_time_seconds": item.prep_time_seconds,
                "display_order": item.display_order
            }
            for item in menu
        ]
    }
