from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from datetime import datetime
from app.database import Base

class Discount(Base):
    """Discount/promo codes"""
    __tablename__ = "discounts"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, default="")
    discount_type = Column(String, default="percent")  # percent, fixed
    amount = Column(Float, nullable=False)  # Percentage or fixed amount
    min_order = Column(Float, default=0.0)  # Minimum order amount
    max_uses = Column(Integer, default=0)  # 0 = unlimited
    times_used = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
