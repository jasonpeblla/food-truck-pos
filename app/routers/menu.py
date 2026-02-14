from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import MenuItem
from app.schemas import MenuItemCreate, MenuItemResponse, MenuItemUpdate

router = APIRouter(prefix="/menu", tags=["menu"])

@router.get("", response_model=List[MenuItemResponse])
def get_menu(category: str = None, available_only: bool = True, db: Session = Depends(get_db)):
    """Get all menu items, optionally filtered by category and availability."""
    query = db.query(MenuItem)
    
    if available_only:
        query = query.filter(MenuItem.is_available == True)
    
    if category:
        query = query.filter(MenuItem.category == category)
    
    return query.order_by(MenuItem.category, MenuItem.display_order).all()

@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """Get all unique categories."""
    categories = db.query(MenuItem.category).distinct().all()
    return [c[0] for c in categories]

@router.get("/search")
def search_menu(q: str, db: Session = Depends(get_db)):
    """Search menu items by name or description."""
    items = db.query(MenuItem).filter(
        (MenuItem.name.ilike(f"%{q}%")) | 
        (MenuItem.description.ilike(f"%{q}%"))
    ).all()
    return items

@router.get("/{item_id}", response_model=MenuItemResponse)
def get_menu_item(item_id: int, db: Session = Depends(get_db)):
    """Get a specific menu item."""
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return item

@router.post("", response_model=MenuItemResponse)
def create_menu_item(item: MenuItemCreate, db: Session = Depends(get_db)):
    """Create a new menu item."""
    db_item = MenuItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.patch("/{item_id}", response_model=MenuItemResponse)
def update_menu_item(item_id: int, update: MenuItemUpdate, db: Session = Depends(get_db)):
    """Update a menu item."""
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    
    db.commit()
    db.refresh(item)
    return item

@router.patch("/{item_id}/toggle-availability", response_model=MenuItemResponse)
def toggle_availability(item_id: int, db: Session = Depends(get_db)):
    """Toggle item availability (sold out / available)."""
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    item.is_available = not item.is_available
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{item_id}")
def delete_menu_item(item_id: int, db: Session = Depends(get_db)):
    """Delete a menu item."""
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    db.delete(item)
    db.commit()
    return {"message": "Menu item deleted"}
