from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from pydantic import BaseModel
from datetime import datetime
from typing import List

from app.database import get_db, Base
from app.models import Order, OrderItem, MenuItem

router = APIRouter(prefix="/offline", tags=["offline"])

class OfflineOrder(Base):
    __tablename__ = "offline_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    local_id = Column(String, nullable=False)  # Client-side UUID
    order_data = Column(Text, nullable=False)  # JSON string
    synced = Column(Boolean, default=False)
    synced_order_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    synced_at = Column(DateTime, nullable=True)

class OfflineOrderCreate(BaseModel):
    local_id: str
    order_data: str  # JSON stringified order

class OfflineBatchSync(BaseModel):
    orders: List[OfflineOrderCreate]

@router.post("/queue")
def queue_offline_order(data: OfflineOrderCreate, db: Session = Depends(get_db)):
    """Queue an order created while offline."""
    existing = db.query(OfflineOrder).filter(
        OfflineOrder.local_id == data.local_id
    ).first()
    
    if existing:
        return {"status": "already_queued", "local_id": data.local_id}
    
    order = OfflineOrder(
        local_id=data.local_id,
        order_data=data.order_data
    )
    db.add(order)
    db.commit()
    
    return {"status": "queued", "local_id": data.local_id}

@router.post("/sync")
def sync_offline_orders(db: Session = Depends(get_db)):
    """Process all queued offline orders."""
    import json
    
    pending = db.query(OfflineOrder).filter(
        OfflineOrder.synced == False
    ).all()
    
    synced = []
    errors = []
    
    for offline in pending:
        try:
            data = json.loads(offline.order_data)
            
            # Create real order
            from app.routers.orders import get_next_order_number, TAX_RATE
            
            order = Order(
                order_number=get_next_order_number(db),
                customer_name=data.get('customer_name', ''),
                notes=data.get('notes', '') + ' [Synced from offline]'
            )
            db.add(order)
            db.flush()
            
            subtotal = 0.0
            for item_data in data.get('items', []):
                menu_item = db.query(MenuItem).filter(
                    MenuItem.id == item_data['menu_item_id']
                ).first()
                
                if menu_item:
                    item_subtotal = menu_item.price * item_data.get('quantity', 1)
                    order_item = OrderItem(
                        order_id=order.id,
                        menu_item_id=menu_item.id,
                        quantity=item_data.get('quantity', 1),
                        unit_price=menu_item.price,
                        subtotal=item_subtotal
                    )
                    db.add(order_item)
                    subtotal += item_subtotal
            
            order.tax = round(subtotal * TAX_RATE, 2)
            order.total = round(subtotal + order.tax, 2)
            
            offline.synced = True
            offline.synced_order_id = order.id
            offline.synced_at = datetime.utcnow()
            
            synced.append({
                "local_id": offline.local_id,
                "order_id": order.id,
                "order_number": order.order_number
            })
            
        except Exception as e:
            errors.append({
                "local_id": offline.local_id,
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "synced_count": len(synced),
        "error_count": len(errors),
        "synced": synced,
        "errors": errors
    }

@router.get("/pending")
def get_pending_offline(db: Session = Depends(get_db)):
    """Get count of pending offline orders."""
    count = db.query(OfflineOrder).filter(
        OfflineOrder.synced == False
    ).count()
    
    return {"pending_count": count}

@router.get("/status")
def offline_status(db: Session = Depends(get_db)):
    """Get offline sync status."""
    total = db.query(OfflineOrder).count()
    synced = db.query(OfflineOrder).filter(OfflineOrder.synced == True).count()
    pending = total - synced
    
    return {
        "total_offline_orders": total,
        "synced": synced,
        "pending": pending,
        "sync_healthy": pending == 0
    }
