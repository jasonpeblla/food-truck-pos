from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, date

from app.database import get_db
from app.models import Order, OrderItem, MenuItem
from app.schemas import OrderCreate, OrderResponse, OrderStatusUpdate, OrderItemResponse, QueueOrderResponse

router = APIRouter(prefix="/orders", tags=["orders"])

TAX_RATE = 0.0875  # 8.75% tax

def get_next_order_number(db: Session) -> int:
    """Get next order number for today (resets daily)."""
    today = date.today()
    last_order = db.query(Order).filter(
        func.date(Order.created_at) == today
    ).order_by(Order.order_number.desc()).first()
    
    return (last_order.order_number + 1) if last_order else 1

def build_order_response(order: Order) -> dict:
    """Build order response with item details."""
    items = []
    for oi in order.items:
        items.append({
            "id": oi.id,
            "menu_item_id": oi.menu_item_id,
            "menu_item_name": oi.menu_item.name if oi.menu_item else "Unknown",
            "quantity": oi.quantity,
            "unit_price": oi.unit_price,
            "subtotal": oi.subtotal,
            "customizations": oi.customizations
        })
    
    return {
        "id": order.id,
        "order_number": order.order_number,
        "customer_name": order.customer_name,
        "status": order.status,
        "total": order.total,
        "tax": order.tax,
        "notes": order.notes,
        "is_paid": order.is_paid,
        "items": items,
        "created_at": order.created_at,
        "completed_at": order.completed_at
    }

@router.get("", response_model=List[OrderResponse])
def get_orders(status: str = None, today_only: bool = True, db: Session = Depends(get_db)):
    """Get orders, optionally filtered by status."""
    query = db.query(Order)
    
    if today_only:
        today = date.today()
        query = query.filter(func.date(Order.created_at) == today)
    
    if status:
        query = query.filter(Order.status == status)
    
    orders = query.order_by(Order.created_at.desc()).all()
    return [build_order_response(o) for o in orders]

@router.get("/queue", response_model=List[QueueOrderResponse])
def get_queue(db: Session = Depends(get_db)):
    """Get customer queue display (pending and preparing orders)."""
    orders = db.query(Order).filter(
        Order.status.in_(["pending", "preparing"])
    ).order_by(Order.created_at).all()
    
    queue = []
    for order in orders:
        # Calculate estimated wait time based on position and prep time
        items_summary = ", ".join([
            f"{oi.quantity}x {oi.menu_item.name}" for oi in order.items[:3]
        ])
        if len(order.items) > 3:
            items_summary += f" +{len(order.items) - 3} more"
        
        # Simple wait time estimation
        total_prep = sum(oi.menu_item.prep_time_seconds * oi.quantity for oi in order.items)
        wait_minutes = max(1, total_prep // 60)
        
        queue.append({
            "order_number": order.order_number,
            "customer_name": order.customer_name or f"Order #{order.order_number}",
            "status": order.status,
            "items_summary": items_summary,
            "wait_time_minutes": wait_minutes
        })
    
    return queue

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Get a specific order."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return build_order_response(order)

@router.post("", response_model=OrderResponse)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    """Create a new order."""
    # Create order
    order = Order(
        order_number=get_next_order_number(db),
        customer_name=order_data.customer_name,
        notes=order_data.notes,
        location_id=order_data.location_id
    )
    db.add(order)
    db.flush()
    
    # Add items
    subtotal = 0.0
    for item_data in order_data.items:
        menu_item = db.query(MenuItem).filter(MenuItem.id == item_data.menu_item_id).first()
        if not menu_item:
            raise HTTPException(status_code=400, detail=f"Menu item {item_data.menu_item_id} not found")
        
        if not menu_item.is_available:
            raise HTTPException(status_code=400, detail=f"{menu_item.name} is not available")
        
        item_subtotal = menu_item.price * item_data.quantity
        
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=menu_item.id,
            quantity=item_data.quantity,
            unit_price=menu_item.price,
            subtotal=item_subtotal,
            customizations=item_data.customizations
        )
        db.add(order_item)
        subtotal += item_subtotal
    
    # Calculate totals
    order.tax = round(subtotal * TAX_RATE, 2)
    order.total = round(subtotal + order.tax, 2)
    
    db.commit()
    db.refresh(order)
    return build_order_response(order)

@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(order_id: int, status_update: OrderStatusUpdate, db: Session = Depends(get_db)):
    """Update order status."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    valid_statuses = ["pending", "preparing", "ready", "completed", "cancelled"]
    if status_update.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    order.status = status_update.status
    
    if status_update.status == "completed":
        order.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(order)
    return build_order_response(order)

@router.delete("/{order_id}")
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    """Cancel an order."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.is_paid:
        raise HTTPException(status_code=400, detail="Cannot cancel a paid order")
    
    order.status = "cancelled"
    db.commit()
    return {"message": "Order cancelled"}
