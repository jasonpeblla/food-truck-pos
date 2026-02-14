from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Ingredient
from app.schemas import IngredientCreate, IngredientResponse, IngredientUpdate

router = APIRouter(prefix="/ingredients", tags=["ingredients"])

def ingredient_to_response(ing: Ingredient) -> dict:
    """Convert ingredient to response with low stock indicator."""
    return {
        "id": ing.id,
        "name": ing.name,
        "unit": ing.unit,
        "stock_quantity": ing.stock_quantity,
        "low_stock_threshold": ing.low_stock_threshold,
        "cost_per_unit": ing.cost_per_unit,
        "is_low_stock": ing.stock_quantity <= ing.low_stock_threshold,
        "created_at": ing.created_at
    }

@router.get("", response_model=List[IngredientResponse])
def get_ingredients(low_stock_only: bool = False, db: Session = Depends(get_db)):
    """Get all ingredients."""
    query = db.query(Ingredient)
    ingredients = query.order_by(Ingredient.name).all()
    
    results = [ingredient_to_response(i) for i in ingredients]
    
    if low_stock_only:
        results = [r for r in results if r["is_low_stock"]]
    
    return results

@router.get("/alerts")
def get_low_stock_alerts(db: Session = Depends(get_db)):
    """Get ingredients that are low on stock."""
    ingredients = db.query(Ingredient).all()
    alerts = []
    
    for ing in ingredients:
        if ing.stock_quantity <= ing.low_stock_threshold:
            alerts.append({
                "id": ing.id,
                "name": ing.name,
                "stock_quantity": ing.stock_quantity,
                "unit": ing.unit,
                "threshold": ing.low_stock_threshold,
                "severity": "critical" if ing.stock_quantity == 0 else "warning"
            })
    
    return alerts

@router.get("/{ingredient_id}", response_model=IngredientResponse)
def get_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    """Get a specific ingredient."""
    ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return ingredient_to_response(ingredient)

@router.post("", response_model=IngredientResponse)
def create_ingredient(ingredient_data: IngredientCreate, db: Session = Depends(get_db)):
    """Create a new ingredient."""
    ingredient = Ingredient(**ingredient_data.model_dump())
    db.add(ingredient)
    db.commit()
    db.refresh(ingredient)
    return ingredient_to_response(ingredient)

@router.patch("/{ingredient_id}", response_model=IngredientResponse)
def update_ingredient(ingredient_id: int, update: IngredientUpdate, db: Session = Depends(get_db)):
    """Update an ingredient."""
    ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ingredient, key, value)
    
    db.commit()
    db.refresh(ingredient)
    return ingredient_to_response(ingredient)

@router.post("/{ingredient_id}/restock")
def restock_ingredient(ingredient_id: int, quantity: float, db: Session = Depends(get_db)):
    """Add stock to an ingredient."""
    ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    
    ingredient.stock_quantity += quantity
    db.commit()
    db.refresh(ingredient)
    return ingredient_to_response(ingredient)

@router.delete("/{ingredient_id}")
def delete_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    """Delete an ingredient."""
    ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    
    db.delete(ingredient)
    db.commit()
    return {"message": "Ingredient deleted"}
