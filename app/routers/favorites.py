from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, func
from datetime import datetime
from typing import List

from app.database import get_db, Base
from app.models import Order, OrderItem, MenuItem

router = APIRouter(prefix="/favorites", tags=["favorites"])

class CustomerFavorite(Base):
    __tablename__ = "customer_favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, index=True, nullable=False)
    menu_item_id = Column(Integer, nullable=False)
    order_count = Column(Integer, default=1)
    last_ordered = Column(DateTime, default=datetime.utcnow)

@router.get("/{phone}")
def get_customer_favorites(phone: str, limit: int = 5, db: Session = Depends(get_db)):
    """Get a customer's frequently ordered items."""
    clean_phone = ''.join(filter(str.isdigit, phone))
    
    favorites = db.query(CustomerFavorite).filter(
        CustomerFavorite.phone == clean_phone
    ).order_by(CustomerFavorite.order_count.desc()).limit(limit).all()
    
    result = []
    for fav in favorites:
        item = db.query(MenuItem).filter(MenuItem.id == fav.menu_item_id).first()
        if item:
            result.append({
                "menu_item_id": item.id,
                "name": item.name,
                "emoji": item.emoji,
                "price": item.price,
                "order_count": fav.order_count,
                "last_ordered": fav.last_ordered.isoformat()
            })
    
    return result

@router.post("/track")
def track_favorite(phone: str, menu_item_id: int, db: Session = Depends(get_db)):
    """Track a customer's order for favorites."""
    clean_phone = ''.join(filter(str.isdigit, phone))
    
    existing = db.query(CustomerFavorite).filter(
        CustomerFavorite.phone == clean_phone,
        CustomerFavorite.menu_item_id == menu_item_id
    ).first()
    
    if existing:
        existing.order_count += 1
        existing.last_ordered = datetime.utcnow()
    else:
        fav = CustomerFavorite(
            phone=clean_phone,
            menu_item_id=menu_item_id
        )
        db.add(fav)
    
    db.commit()
    return {"tracked": True}

@router.get("/popular/all")
def get_popular_items(days: int = 7, limit: int = 10, db: Session = Depends(get_db)):
    """Get most popular items across all customers."""
    from datetime import timedelta
    since = datetime.utcnow() - timedelta(days=days)
    
    # Get order items from recent orders
    popular = db.query(
        OrderItem.menu_item_id,
        func.sum(OrderItem.quantity).label('total_qty')
    ).join(Order).filter(
        Order.created_at >= since,
        Order.status.in_(['completed', 'ready'])
    ).group_by(OrderItem.menu_item_id).order_by(
        func.sum(OrderItem.quantity).desc()
    ).limit(limit).all()
    
    result = []
    for item_id, total_qty in popular:
        item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
        if item:
            result.append({
                "id": item.id,
                "name": item.name,
                "emoji": item.emoji,
                "category": item.category,
                "orders": total_qty
            })
    
    return result
