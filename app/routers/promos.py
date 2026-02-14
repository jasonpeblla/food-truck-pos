from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

from app.database import get_db, Base

router = APIRouter(prefix="/promos", tags=["promos"])

class PromoCode(Base):
    __tablename__ = "promo_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, default="")
    discount_type = Column(String, default="percent")  # percent or fixed
    discount_value = Column(Float, default=10.0)  # 10% or $10
    min_order = Column(Float, default=0.0)  # Minimum order amount
    max_uses = Column(Integer, default=100)
    times_used = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    source = Column(String, default="manual")  # manual, social, event
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

class PromoCreate(BaseModel):
    code: str
    description: str = ""
    discount_type: str = "percent"
    discount_value: float = 10.0
    min_order: float = 0.0
    max_uses: int = 100
    source: str = "manual"
    expires_at: Optional[str] = None

class PromoResponse(BaseModel):
    id: int
    code: str
    description: str
    discount_type: str
    discount_value: float
    min_order: float
    times_used: int
    max_uses: int
    is_active: bool
    source: str
    
    class Config:
        from_attributes = True

class PromoValidateResponse(BaseModel):
    valid: bool
    code: str
    discount_type: str
    discount_value: float
    message: str
    calculated_discount: float

@router.post("", response_model=PromoResponse)
def create_promo(data: PromoCreate, db: Session = Depends(get_db)):
    """Create a new promo code."""
    existing = db.query(PromoCode).filter(PromoCode.code == data.code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Promo code already exists")
    
    expires = None
    if data.expires_at:
        try:
            expires = datetime.fromisoformat(data.expires_at.replace('Z', '+00:00'))
        except:
            pass
    
    promo = PromoCode(
        code=data.code.upper(),
        description=data.description,
        discount_type=data.discount_type,
        discount_value=data.discount_value,
        min_order=data.min_order,
        max_uses=data.max_uses,
        source=data.source,
        expires_at=expires
    )
    db.add(promo)
    db.commit()
    db.refresh(promo)
    return promo

@router.get("", response_model=List[PromoResponse])
def get_promos(active_only: bool = True, db: Session = Depends(get_db)):
    """Get all promo codes."""
    query = db.query(PromoCode)
    if active_only:
        query = query.filter(PromoCode.is_active == True)
    return query.all()

@router.post("/validate")
def validate_promo(code: str, order_total: float = 0, db: Session = Depends(get_db)):
    """Validate a promo code and calculate discount."""
    promo = db.query(PromoCode).filter(PromoCode.code == code.upper()).first()
    
    if not promo:
        return {"valid": False, "code": code, "message": "Invalid promo code", "calculated_discount": 0}
    
    if not promo.is_active:
        return {"valid": False, "code": code, "message": "Promo code is no longer active", "calculated_discount": 0}
    
    if promo.times_used >= promo.max_uses:
        return {"valid": False, "code": code, "message": "Promo code has been fully redeemed", "calculated_discount": 0}
    
    if promo.expires_at and datetime.utcnow() > promo.expires_at:
        return {"valid": False, "code": code, "message": "Promo code has expired", "calculated_discount": 0}
    
    if order_total < promo.min_order:
        return {"valid": False, "code": code, "message": f"Minimum order ${promo.min_order:.2f} required", "calculated_discount": 0}
    
    # Calculate discount
    if promo.discount_type == "percent":
        discount = round(order_total * (promo.discount_value / 100), 2)
    else:
        discount = min(promo.discount_value, order_total)
    
    return {
        "valid": True,
        "code": promo.code,
        "discount_type": promo.discount_type,
        "discount_value": promo.discount_value,
        "message": f"{promo.discount_value}{'%' if promo.discount_type == 'percent' else ' off'} applied!",
        "calculated_discount": discount
    }

@router.post("/redeem/{code}")
def redeem_promo(code: str, db: Session = Depends(get_db)):
    """Mark a promo code as used."""
    promo = db.query(PromoCode).filter(PromoCode.code == code.upper()).first()
    if not promo:
        raise HTTPException(status_code=404, detail="Promo code not found")
    
    promo.times_used += 1
    if promo.times_used >= promo.max_uses:
        promo.is_active = False
    
    db.commit()
    return {"redeemed": True, "times_used": promo.times_used}

@router.get("/social-share")
def get_social_share_text():
    """Get social media share text with current promo."""
    # This would integrate with active promos
    return {
        "twitter": "🌮 Getting amazing tacos from @FoodTruckPOS! Use code SOCIAL10 for 10% off! #FoodTruck #Tacos",
        "instagram": "Best tacos in town! 🌮🔥 Use code SOCIAL10 for 10% off your order!",
        "facebook": "Just had the most amazing tacos! 🌮 You can use code SOCIAL10 for 10% off. Trust me, it's worth it!",
        "share_url": "https://foodtruck.example.com",
        "active_code": "SOCIAL10"
    }

@router.post("/generate-social")
def generate_social_promo(db: Session = Depends(get_db)):
    """Generate a social media promo code."""
    code = "SOCIAL10"
    existing = db.query(PromoCode).filter(PromoCode.code == code).first()
    if existing:
        return {"code": code, "message": "Social promo already exists"}
    
    promo = PromoCode(
        code=code,
        description="Social media share discount",
        discount_type="percent",
        discount_value=10.0,
        max_uses=1000,
        source="social"
    )
    db.add(promo)
    db.commit()
    
    return {"code": code, "discount": "10%", "message": "Social promo created!"}
