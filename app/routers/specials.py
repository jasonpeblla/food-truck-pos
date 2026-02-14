from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional

from app.database import get_db, Base
from app.models import MenuItem

router = APIRouter(prefix="/specials", tags=["specials"])

class DailySpecial(Base):
    __tablename__ = "daily_specials"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False)
    menu_item_id = Column(Integer, nullable=False)
    special_price = Column(Float, nullable=False)
    description = Column(String, default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SpecialCreate(BaseModel):
    menu_item_id: int
    special_price: float
    description: str = ""
    date: Optional[str] = None  # ISO date, defaults to today

@router.post("")
def create_special(data: SpecialCreate, db: Session = Depends(get_db)):
    """Create a daily special."""
    target_date = datetime.strptime(data.date, "%Y-%m-%d") if data.date else datetime.now()
    
    # Verify menu item exists
    item = db.query(MenuItem).filter(MenuItem.id == data.menu_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    special = DailySpecial(
        date=target_date,
        menu_item_id=data.menu_item_id,
        special_price=data.special_price,
        description=data.description
    )
    db.add(special)
    db.commit()
    db.refresh(special)
    
    return {
        "id": special.id,
        "item": item.name,
        "original_price": item.price,
        "special_price": special.special_price,
        "savings": round(item.price - special.special_price, 2),
        "date": str(target_date.date())
    }

@router.get("/today")
def get_today_specials(db: Session = Depends(get_db)):
    """Get today's specials."""
    today = date.today()
    
    specials = db.query(DailySpecial).filter(
        DailySpecial.date >= datetime(today.year, today.month, today.day),
        DailySpecial.date < datetime(today.year, today.month, today.day + 1),
        DailySpecial.is_active == True
    ).all()
    
    result = []
    for special in specials:
        item = db.query(MenuItem).filter(MenuItem.id == special.menu_item_id).first()
        if item:
            result.append({
                "id": special.id,
                "menu_item_id": item.id,
                "name": item.name,
                "emoji": item.emoji,
                "category": item.category,
                "original_price": item.price,
                "special_price": special.special_price,
                "savings": round(item.price - special.special_price, 2),
                "description": special.description
            })
    
    return result

@router.get("/upcoming")
def get_upcoming_specials(days: int = 7, db: Session = Depends(get_db)):
    """Get upcoming specials."""
    from datetime import timedelta
    
    today = date.today()
    future = datetime.now() + timedelta(days=days)
    
    specials = db.query(DailySpecial).filter(
        DailySpecial.date >= datetime(today.year, today.month, today.day),
        DailySpecial.date <= future,
        DailySpecial.is_active == True
    ).order_by(DailySpecial.date).all()
    
    result = []
    for special in specials:
        item = db.query(MenuItem).filter(MenuItem.id == special.menu_item_id).first()
        if item:
            result.append({
                "date": special.date.strftime("%Y-%m-%d"),
                "item": item.name,
                "special_price": special.special_price
            })
    
    return result

@router.delete("/{special_id}")
def delete_special(special_id: int, db: Session = Depends(get_db)):
    """Delete a special."""
    special = db.query(DailySpecial).filter(DailySpecial.id == special_id).first()
    if not special:
        raise HTTPException(status_code=404, detail="Special not found")
    
    special.is_active = False
    db.commit()
    return {"deleted": True}
