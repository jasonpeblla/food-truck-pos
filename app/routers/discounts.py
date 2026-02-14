from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.discount import Discount

router = APIRouter(prefix="/discounts", tags=["discounts"])

class DiscountCreate(BaseModel):
    code: str
    description: str = ""
    discount_type: str = "percent"
    amount: float
    min_order: float = 0.0
    max_uses: int = 0
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

class DiscountResponse(BaseModel):
    id: int
    code: str
    description: str
    discount_type: str
    amount: float
    min_order: float
    max_uses: int
    times_used: int
    is_active: bool
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    
    class Config:
        from_attributes = True

class DiscountValidation(BaseModel):
    valid: bool
    message: str
    discount_amount: float = 0
    discount_type: str = ""

@router.get("", response_model=List[DiscountResponse])
def get_discounts(active_only: bool = True, db: Session = Depends(get_db)):
    """Get all discounts."""
    query = db.query(Discount)
    if active_only:
        query = query.filter(Discount.is_active == True)
    return query.order_by(Discount.created_at.desc()).all()

@router.post("", response_model=DiscountResponse)
def create_discount(discount_data: DiscountCreate, db: Session = Depends(get_db)):
    """Create a new discount code."""
    # Check for duplicate code
    existing = db.query(Discount).filter(Discount.code == discount_data.code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Discount code already exists")
    
    discount = Discount(
        **discount_data.model_dump(),
        code=discount_data.code.upper()
    )
    db.add(discount)
    db.commit()
    db.refresh(discount)
    return discount

@router.get("/validate/{code}")
def validate_discount(code: str, order_total: float = 0, db: Session = Depends(get_db)):
    """Validate a discount code."""
    discount = db.query(Discount).filter(
        Discount.code == code.upper(),
        Discount.is_active == True
    ).first()
    
    if not discount:
        return DiscountValidation(valid=False, message="Invalid discount code")
    
    now = datetime.utcnow()
    
    # Check validity period
    if discount.valid_from and now < discount.valid_from:
        return DiscountValidation(valid=False, message="Discount not yet active")
    
    if discount.valid_until and now > discount.valid_until:
        return DiscountValidation(valid=False, message="Discount has expired")
    
    # Check usage limit
    if discount.max_uses > 0 and discount.times_used >= discount.max_uses:
        return DiscountValidation(valid=False, message="Discount usage limit reached")
    
    # Check minimum order
    if order_total < discount.min_order:
        return DiscountValidation(
            valid=False, 
            message=f"Minimum order of ${discount.min_order:.2f} required"
        )
    
    # Calculate discount amount
    if discount.discount_type == "percent":
        discount_amount = order_total * (discount.amount / 100)
    else:
        discount_amount = min(discount.amount, order_total)
    
    return DiscountValidation(
        valid=True,
        message=f"Discount applied: {discount.description or discount.code}",
        discount_amount=round(discount_amount, 2),
        discount_type=discount.discount_type
    )

@router.post("/use/{code}")
def use_discount(code: str, db: Session = Depends(get_db)):
    """Mark a discount as used (increment counter)."""
    discount = db.query(Discount).filter(Discount.code == code.upper()).first()
    if not discount:
        raise HTTPException(status_code=404, detail="Discount not found")
    
    discount.times_used += 1
    db.commit()
    return {"message": "Discount usage recorded"}

@router.patch("/{discount_id}/toggle")
def toggle_discount(discount_id: int, db: Session = Depends(get_db)):
    """Toggle discount active status."""
    discount = db.query(Discount).filter(Discount.id == discount_id).first()
    if not discount:
        raise HTTPException(status_code=404, detail="Discount not found")
    
    discount.is_active = not discount.is_active
    db.commit()
    return {"id": discount.id, "is_active": discount.is_active}

@router.delete("/{discount_id}")
def delete_discount(discount_id: int, db: Session = Depends(get_db)):
    """Delete a discount."""
    discount = db.query(Discount).filter(Discount.id == discount_id).first()
    if not discount:
        raise HTTPException(status_code=404, detail="Discount not found")
    
    db.delete(discount)
    db.commit()
    return {"message": "Discount deleted"}
