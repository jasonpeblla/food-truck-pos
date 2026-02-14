from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime
from app.database import Base

class Shift(Base):
    """Track staff shifts and drawer reconciliation"""
    __tablename__ = "shifts"
    
    id = Column(Integer, primary_key=True, index=True)
    staff_name = Column(String, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Cash drawer
    starting_cash = Column(Float, default=0.0)
    ending_cash = Column(Float, nullable=True)
    expected_cash = Column(Float, nullable=True)
    
    # Shift totals (calculated at close)
    total_orders = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)
    total_tips = Column(Float, default=0.0)
    cash_sales = Column(Float, default=0.0)
    card_sales = Column(Float, default=0.0)
    
    notes = Column(String, default="")
