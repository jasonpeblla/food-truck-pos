from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import date

from app.database import get_db

router = APIRouter(prefix="/prep", tags=["prep"])

# In-memory storage for prep checklist (resets daily)
# In production, this would be in the database
_prep_items = {}
_last_date = None

DEFAULT_CHECKLIST = [
    {"id": 1, "category": "Equipment", "item": "Generator running / power connected", "checked": False},
    {"id": 2, "category": "Equipment", "item": "POS system powered on", "checked": False},
    {"id": 3, "category": "Equipment", "item": "Card reader connected", "checked": False},
    {"id": 4, "category": "Equipment", "item": "Grill/cooking equipment heated", "checked": False},
    {"id": 5, "category": "Equipment", "item": "Refrigeration temperature OK", "checked": False},
    {"id": 6, "category": "Supplies", "item": "Cash drawer stocked", "checked": False},
    {"id": 7, "category": "Supplies", "item": "Receipt paper loaded", "checked": False},
    {"id": 8, "category": "Supplies", "item": "To-go containers ready", "checked": False},
    {"id": 9, "category": "Supplies", "item": "Napkins & utensils stocked", "checked": False},
    {"id": 10, "category": "Food", "item": "Protein thawed/prepped", "checked": False},
    {"id": 11, "category": "Food", "item": "Vegetables chopped", "checked": False},
    {"id": 12, "category": "Food", "item": "Sauces/condiments filled", "checked": False},
    {"id": 13, "category": "Food", "item": "Check ingredient stock levels", "checked": False},
    {"id": 14, "category": "Safety", "item": "Handwashing station ready", "checked": False},
    {"id": 15, "category": "Safety", "item": "Fire extinguisher accessible", "checked": False},
    {"id": 16, "category": "Safety", "item": "First aid kit stocked", "checked": False},
]

def get_checklist() -> List[dict]:
    """Get today's checklist, resetting if new day."""
    global _prep_items, _last_date
    
    today = date.today()
    if _last_date != today:
        _prep_items = {item["id"]: dict(item) for item in DEFAULT_CHECKLIST}
        _last_date = today
    
    return list(_prep_items.values())

class CheckItemRequest(BaseModel):
    checked: bool

@router.get("")
def get_prep_checklist():
    """Get the daily prep checklist."""
    items = get_checklist()
    categories = {}
    for item in items:
        cat = item["category"]
        if cat not in categories:
            categories[cat] = {"name": cat, "items": [], "completed": 0, "total": 0}
        categories[cat]["items"].append(item)
        categories[cat]["total"] += 1
        if item["checked"]:
            categories[cat]["completed"] += 1
    
    total = len(items)
    completed = len([i for i in items if i["checked"]])
    
    return {
        "date": date.today().isoformat(),
        "categories": list(categories.values()),
        "total": total,
        "completed": completed,
        "progress_percent": round((completed / total) * 100) if total > 0 else 0
    }

@router.post("/{item_id}/toggle")
def toggle_prep_item(item_id: int):
    """Toggle a prep item's checked status."""
    items = get_checklist()
    
    if item_id not in _prep_items:
        return {"error": "Item not found"}
    
    _prep_items[item_id]["checked"] = not _prep_items[item_id]["checked"]
    
    return _prep_items[item_id]

@router.post("/reset")
def reset_checklist():
    """Reset the checklist (uncheck all items)."""
    global _prep_items
    
    for item_id in _prep_items:
        _prep_items[item_id]["checked"] = False
    
    return {"message": "Checklist reset", "items": list(_prep_items.values())}
