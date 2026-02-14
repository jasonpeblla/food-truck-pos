from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, date
import json
import asyncio

from app.database import get_db, SessionLocal
from app.models import Order, OrderItem

router = APIRouter(prefix="/kitchen", tags=["kitchen"])

# Active WebSocket connections for kitchen display
active_connections: List[WebSocket] = []

async def broadcast_orders():
    """Broadcast current orders to all connected kitchen displays."""
    db = SessionLocal()
    try:
        orders = db.query(Order).filter(
            Order.status.in_(["pending", "preparing"]),
            func.date(Order.created_at) == date.today()
        ).order_by(Order.created_at).all()
        
        data = []
        for order in orders:
            elapsed = (datetime.utcnow() - order.created_at).total_seconds()
            data.append({
                "id": order.id,
                "order_number": order.order_number,
                "customer_name": order.customer_name or f"Order #{order.order_number}",
                "status": order.status,
                "elapsed_seconds": int(elapsed),
                "items": [
                    {
                        "name": oi.menu_item.name,
                        "quantity": oi.quantity,
                        "customizations": oi.customizations
                    }
                    for oi in order.items
                ]
            })
        
        message = json.dumps({"type": "orders", "data": data})
        for connection in active_connections:
            try:
                await connection.send_text(message)
            except:
                pass
    finally:
        db.close()

@router.websocket("/ws")
async def kitchen_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time kitchen display updates."""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Send initial orders
        await broadcast_orders()
        
        # Keep connection alive
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                # Handle bump commands
                if data.startswith("bump:"):
                    order_id = int(data.split(":")[1])
                    db = SessionLocal()
                    order = db.query(Order).filter(Order.id == order_id).first()
                    if order:
                        if order.status == "pending":
                            order.status = "preparing"
                        elif order.status == "preparing":
                            order.status = "ready"
                        db.commit()
                    db.close()
                    await broadcast_orders()
            except asyncio.TimeoutError:
                # Send ping to keep alive
                await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)

@router.get("/orders")
def get_kitchen_orders(db: Session = Depends(get_db)):
    """Get orders for kitchen display (HTTP fallback)."""
    orders = db.query(Order).filter(
        Order.status.in_(["pending", "preparing"]),
        func.date(Order.created_at) == date.today()
    ).order_by(Order.created_at).all()
    
    result = []
    for order in orders:
        elapsed = (datetime.utcnow() - order.created_at).total_seconds()
        result.append({
            "id": order.id,
            "order_number": order.order_number,
            "customer_name": order.customer_name or f"Order #{order.order_number}",
            "status": order.status,
            "elapsed_seconds": int(elapsed),
            "items": [
                {
                    "name": oi.menu_item.name,
                    "quantity": oi.quantity,
                    "customizations": oi.customizations
                }
                for oi in order.items
            ]
        })
    
    return result

@router.post("/bump/{order_id}")
async def bump_order(order_id: int, db: Session = Depends(get_db)):
    """Bump an order to the next status."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"error": "Order not found"}
    
    if order.status == "pending":
        order.status = "preparing"
    elif order.status == "preparing":
        order.status = "ready"
    
    db.commit()
    
    # Broadcast update
    await broadcast_orders()
    
    return {"id": order.id, "status": order.status}
