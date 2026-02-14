from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.models import Customer

router = APIRouter(prefix="/customers", tags=["customers"])

# Points config
POINTS_PER_DOLLAR = 1  # 1 point per $1 spent
POINTS_TO_REDEEM = 50  # 50 points = $5 reward
REWARD_VALUE = 5.00  # $5 off

class CustomerLookup(BaseModel):
    phone: str

class CustomerCreate(BaseModel):
    phone: str
    name: str = ""

class CustomerResponse(BaseModel):
    id: int
    phone: str
    name: str
    points: int
    total_visits: int
    total_spent: float
    can_redeem: bool
    reward_value: float
    points_to_next_reward: int
    
    class Config:
        from_attributes = True

def build_customer_response(customer: Customer) -> dict:
    can_redeem = customer.points >= POINTS_TO_REDEEM
    points_to_next = max(0, POINTS_TO_REDEEM - customer.points)
    
    return {
        "id": customer.id,
        "phone": customer.phone,
        "name": customer.name,
        "points": customer.points,
        "total_visits": customer.total_visits,
        "total_spent": customer.total_spent,
        "can_redeem": can_redeem,
        "reward_value": REWARD_VALUE if can_redeem else 0,
        "points_to_next_reward": points_to_next
    }

@router.get("/lookup/{phone}", response_model=CustomerResponse)
def lookup_customer(phone: str, db: Session = Depends(get_db)):
    """Look up a customer by phone number."""
    # Normalize phone (remove non-digits)
    clean_phone = ''.join(filter(str.isdigit, phone))
    
    customer = db.query(Customer).filter(Customer.phone == clean_phone).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return build_customer_response(customer)

@router.post("/register", response_model=CustomerResponse)
def register_customer(data: CustomerCreate, db: Session = Depends(get_db)):
    """Register a new loyalty customer."""
    clean_phone = ''.join(filter(str.isdigit, data.phone))
    
    if len(clean_phone) < 10:
        raise HTTPException(status_code=400, detail="Invalid phone number")
    
    # Check if already exists
    existing = db.query(Customer).filter(Customer.phone == clean_phone).first()
    if existing:
        return build_customer_response(existing)
    
    customer = Customer(
        phone=clean_phone,
        name=data.name
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    
    return build_customer_response(customer)

@router.post("/{customer_id}/add-points")
def add_points(customer_id: int, amount: float, db: Session = Depends(get_db)):
    """Add points based on purchase amount."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    points_earned = int(amount * POINTS_PER_DOLLAR)
    customer.points += points_earned
    customer.total_visits += 1
    customer.total_spent += amount
    customer.last_visit = datetime.utcnow()
    
    db.commit()
    
    return {
        "points_earned": points_earned,
        "total_points": customer.points,
        "can_redeem": customer.points >= POINTS_TO_REDEEM
    }

@router.post("/{customer_id}/redeem")
def redeem_points(customer_id: int, db: Session = Depends(get_db)):
    """Redeem points for reward."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if customer.points < POINTS_TO_REDEEM:
        raise HTTPException(
            status_code=400, 
            detail=f"Need {POINTS_TO_REDEEM - customer.points} more points"
        )
    
    customer.points -= POINTS_TO_REDEEM
    db.commit()
    
    return {
        "reward_applied": REWARD_VALUE,
        "remaining_points": customer.points,
        "message": f"${REWARD_VALUE:.2f} reward applied!"
    }

@router.get("/config")
def get_loyalty_config():
    """Get loyalty program configuration."""
    return {
        "points_per_dollar": POINTS_PER_DOLLAR,
        "points_to_redeem": POINTS_TO_REDEEM,
        "reward_value": REWARD_VALUE
    }
