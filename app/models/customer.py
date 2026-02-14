from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime
from app.database import Base

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, default="")
    points = Column(Integer, default=0)  # Loyalty points
    total_visits = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    last_visit = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Points settings: 1 point per dollar spent
    # 50 points = $5 off
