from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text
from pydantic import BaseModel
from typing import List

from app.database import get_db, Base
from app.models import MenuItem

router = APIRouter(prefix="/shortcuts", tags=["shortcuts"])

class QuickAction(Base):
    __tablename__ = "quick_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    action_type = Column(String, nullable=False)  # combo, discount, message
    config = Column(Text, default="{}")  # JSON config
    display_order = Column(Integer, default=0)
    emoji = Column(String, default="⚡")
    color = Column(String, default="orange")

class QuickActionCreate(BaseModel):
    name: str
    action_type: str
    config: str = "{}"
    emoji: str = "⚡"
    color: str = "orange"

@router.get("")
def get_quick_actions(db: Session = Depends(get_db)):
    """Get all quick actions."""
    actions = db.query(QuickAction).order_by(QuickAction.display_order).all()
    return [{
        "id": a.id,
        "name": a.name,
        "action_type": a.action_type,
        "config": a.config,
        "emoji": a.emoji,
        "color": a.color
    } for a in actions]

@router.post("")
def create_quick_action(data: QuickActionCreate, db: Session = Depends(get_db)):
    """Create a quick action."""
    action = QuickAction(
        name=data.name,
        action_type=data.action_type,
        config=data.config,
        emoji=data.emoji,
        color=data.color
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return action

@router.get("/combos")
def get_popular_combos(db: Session = Depends(get_db)):
    """Get suggested combo deals."""
    # Get most popular items
    items = db.query(MenuItem).filter(
        MenuItem.is_available == True
    ).all()
    
    # Generate combo suggestions
    combos = []
    
    # Taco + Drink combo
    tacos = [i for i in items if i.category == 'tacos']
    drinks = [i for i in items if i.category == 'drinks']
    
    if tacos and drinks:
        combos.append({
            "name": "Taco + Drink Deal",
            "items": [tacos[0].id, drinks[0].id],
            "original_price": tacos[0].price + drinks[0].price,
            "combo_price": round((tacos[0].price + drinks[0].price) * 0.9, 2),
            "savings": round((tacos[0].price + drinks[0].price) * 0.1, 2)
        })
    
    # Burrito + Side combo
    burritos = [i for i in items if i.category == 'burritos']
    sides = [i for i in items if i.category == 'sides']
    
    if burritos and sides:
        combos.append({
            "name": "Burrito + Side Deal",
            "items": [burritos[0].id, sides[0].id],
            "original_price": burritos[0].price + sides[0].price,
            "combo_price": round((burritos[0].price + sides[0].price) * 0.85, 2),
            "savings": round((burritos[0].price + sides[0].price) * 0.15, 2)
        })
    
    return combos

@router.get("/defaults")
def get_default_shortcuts():
    """Get default quick action shortcuts."""
    return [
        {"name": "Repeat Last", "emoji": "🔄", "action": "repeat_last"},
        {"name": "Quick Cash $20", "emoji": "💵", "action": "quick_cash_20"},
        {"name": "Add Note", "emoji": "📝", "action": "add_note"},
        {"name": "Mark Sold Out", "emoji": "🚫", "action": "sold_out"},
        {"name": "Call Order Ready", "emoji": "📢", "action": "call_ready"},
        {"name": "Print Receipt", "emoji": "🖨️", "action": "print_receipt"}
    ]
