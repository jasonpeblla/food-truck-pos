from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class ModifierGroup(Base):
    """Group of modifiers (e.g., "Toppings", "Sauces", "Size")"""
    __tablename__ = "modifier_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # e.g., "Extra Toppings"
    required = Column(Boolean, default=False)
    max_selections = Column(Integer, default=0)  # 0 = unlimited
    created_at = Column(DateTime, default=datetime.utcnow)
    
    modifiers = relationship("Modifier", back_populates="group")

class Modifier(Base):
    """Individual modifier option"""
    __tablename__ = "modifiers"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("modifier_groups.id"), nullable=False)
    name = Column(String, nullable=False)  # e.g., "Extra Cheese"
    price = Column(Float, default=0.0)  # Additional cost
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    group = relationship("ModifierGroup", back_populates="modifiers")
