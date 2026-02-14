from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class MenuItem(Base):
    __tablename__ = "menu_items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # e.g., "tacos", "drinks", "sides"
    price = Column(Float, nullable=False)
    description = Column(String, default="")
    is_available = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    emoji = Column(String, default="🍽️")
    photo_url = Column(String, default="")  # URL to item photo
    prep_time_seconds = Column(Integer, default=120)  # 2 min default
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="menu_item")
    ingredients = relationship("MenuItemIngredient", back_populates="menu_item")
