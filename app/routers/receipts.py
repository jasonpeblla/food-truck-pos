from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import Order, Payment, Location

router = APIRouter(prefix="/receipts", tags=["receipts"])

@router.get("/{order_id}")
def get_receipt(order_id: int, db: Session = Depends(get_db)):
    """Generate receipt data for an order."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    
    # Get active location
    location = db.query(Location).filter(Location.is_active == True).first()
    
    items = []
    for oi in order.items:
        items.append({
            "name": oi.menu_item.name,
            "quantity": oi.quantity,
            "unit_price": oi.unit_price,
            "subtotal": oi.subtotal
        })
    
    subtotal = sum(i["subtotal"] for i in items)
    
    receipt = {
        "business_name": "Food Truck POS",
        "location": location.name if location else "Mobile",
        "address": location.address if location else "",
        "order_number": order.order_number,
        "date": order.created_at.strftime("%Y-%m-%d"),
        "time": order.created_at.strftime("%H:%M:%S"),
        "customer_name": order.customer_name or "Guest",
        "items": items,
        "subtotal": subtotal,
        "tax": order.tax,
        "total": order.total,
        "payment": {
            "method": payment.method if payment else None,
            "tip": payment.tip if payment else 0,
            "total_paid": (payment.amount + payment.tip) if payment else 0,
            "change": payment.change_given if payment else 0
        } if payment else None,
        "footer": "Thank you for your order!",
        "is_paid": order.is_paid
    }
    
    return receipt

@router.get("/{order_id}/text")
def get_receipt_text(order_id: int, db: Session = Depends(get_db)):
    """Generate printable text receipt."""
    receipt = get_receipt(order_id, db)
    
    lines = []
    lines.append("=" * 32)
    lines.append(receipt["business_name"].center(32))
    lines.append(receipt["location"].center(32))
    if receipt["address"]:
        lines.append(receipt["address"].center(32))
    lines.append("=" * 32)
    lines.append(f"Order: #{receipt['order_number']}")
    lines.append(f"Date: {receipt['date']} {receipt['time']}")
    lines.append(f"Customer: {receipt['customer_name']}")
    lines.append("-" * 32)
    
    for item in receipt["items"]:
        lines.append(f"{item['quantity']}x {item['name']}")
        lines.append(f"   ${item['unit_price']:.2f} ea   ${item['subtotal']:.2f}".rjust(32))
    
    lines.append("-" * 32)
    lines.append(f"{'Subtotal:':<20}${receipt['subtotal']:>10.2f}")
    lines.append(f"{'Tax:':<20}${receipt['tax']:>10.2f}")
    lines.append(f"{'TOTAL:':<20}${receipt['total']:>10.2f}")
    
    if receipt["payment"]:
        lines.append("-" * 32)
        lines.append(f"Payment: {receipt['payment']['method'].upper()}")
        if receipt["payment"]["tip"] > 0:
            lines.append(f"{'Tip:':<20}${receipt['payment']['tip']:>10.2f}")
        lines.append(f"{'Amount Paid:':<20}${receipt['payment']['total_paid']:>10.2f}")
        if receipt["payment"]["change"] > 0:
            lines.append(f"{'Change:':<20}${receipt['payment']['change']:>10.2f}")
    
    lines.append("=" * 32)
    lines.append(receipt["footer"].center(32))
    lines.append("=" * 32)
    
    return {"text": "\n".join(lines)}
