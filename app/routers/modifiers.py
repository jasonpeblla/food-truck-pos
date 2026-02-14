from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import ModifierGroup, Modifier

router = APIRouter(prefix="/modifiers", tags=["modifiers"])

# Schemas
class ModifierCreate(BaseModel):
    name: str
    price: float = 0.0

class ModifierGroupCreate(BaseModel):
    name: str
    required: bool = False
    max_selections: int = 0

class ModifierResponse(BaseModel):
    id: int
    name: str
    price: float
    is_available: bool
    
    class Config:
        from_attributes = True

class ModifierGroupResponse(BaseModel):
    id: int
    name: str
    required: bool
    max_selections: int
    modifiers: List[ModifierResponse]
    
    class Config:
        from_attributes = True

@router.get("", response_model=List[ModifierGroupResponse])
def get_modifier_groups(db: Session = Depends(get_db)):
    """Get all modifier groups with their modifiers."""
    return db.query(ModifierGroup).all()

@router.post("/groups", response_model=ModifierGroupResponse)
def create_modifier_group(group_data: ModifierGroupCreate, db: Session = Depends(get_db)):
    """Create a new modifier group."""
    group = ModifierGroup(**group_data.model_dump())
    db.add(group)
    db.commit()
    db.refresh(group)
    return group

@router.post("/groups/{group_id}/modifiers", response_model=ModifierResponse)
def add_modifier_to_group(group_id: int, modifier_data: ModifierCreate, db: Session = Depends(get_db)):
    """Add a modifier to a group."""
    group = db.query(ModifierGroup).filter(ModifierGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Modifier group not found")
    
    modifier = Modifier(group_id=group_id, **modifier_data.model_dump())
    db.add(modifier)
    db.commit()
    db.refresh(modifier)
    return modifier

@router.patch("/items/{modifier_id}/toggle")
def toggle_modifier_availability(modifier_id: int, db: Session = Depends(get_db)):
    """Toggle modifier availability."""
    modifier = db.query(Modifier).filter(Modifier.id == modifier_id).first()
    if not modifier:
        raise HTTPException(status_code=404, detail="Modifier not found")
    
    modifier.is_available = not modifier.is_available
    db.commit()
    return {"id": modifier.id, "is_available": modifier.is_available}

@router.delete("/groups/{group_id}")
def delete_modifier_group(group_id: int, db: Session = Depends(get_db)):
    """Delete a modifier group."""
    group = db.query(ModifierGroup).filter(ModifierGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Modifier group not found")
    
    db.delete(group)
    db.commit()
    return {"message": "Modifier group deleted"}
