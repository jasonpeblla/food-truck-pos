from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, Float, String, DateTime, func
from datetime import datetime, date
from pydantic import BaseModel
from typing import Optional

from app.database import get_db, Base
from app.models import Order

router = APIRouter(prefix="/goals", tags=["goals"])

class DailyGoal(Base):
    __tablename__ = "daily_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, unique=True)
    revenue_target = Column(Float, default=500.0)
    orders_target = Column(Integer, default=50)
    created_at = Column(DateTime, default=datetime.utcnow)

class GoalSet(BaseModel):
    revenue_target: float = 500.0
    orders_target: int = 50

@router.get("/today")
def get_today_goal(db: Session = Depends(get_db)):
    """Get today's goal and progress."""
    today = date.today()
    
    # Get or create today's goal
    goal = db.query(DailyGoal).filter(
        func.date(DailyGoal.date) == today
    ).first()
    
    if not goal:
        goal = DailyGoal(date=datetime.now(), revenue_target=500.0, orders_target=50)
        db.add(goal)
        db.commit()
        db.refresh(goal)
    
    # Get current progress
    orders = db.query(Order).filter(
        func.date(Order.created_at) == today,
        Order.is_paid == True
    ).all()
    
    current_revenue = sum(o.total for o in orders)
    current_orders = len(orders)
    
    revenue_progress = min(100, round(current_revenue / goal.revenue_target * 100, 1))
    orders_progress = min(100, round(current_orders / goal.orders_target * 100, 1))
    
    return {
        "date": str(today),
        "targets": {
            "revenue": goal.revenue_target,
            "orders": goal.orders_target
        },
        "current": {
            "revenue": round(current_revenue, 2),
            "orders": current_orders
        },
        "progress": {
            "revenue_percent": revenue_progress,
            "orders_percent": orders_progress
        },
        "status": "goal_reached" if revenue_progress >= 100 else "in_progress",
        "remaining": {
            "revenue": max(0, round(goal.revenue_target - current_revenue, 2)),
            "orders": max(0, goal.orders_target - current_orders)
        }
    }

@router.post("/today")
def set_today_goal(data: GoalSet, db: Session = Depends(get_db)):
    """Set today's goal."""
    today = date.today()
    
    goal = db.query(DailyGoal).filter(
        func.date(DailyGoal.date) == today
    ).first()
    
    if goal:
        goal.revenue_target = data.revenue_target
        goal.orders_target = data.orders_target
    else:
        goal = DailyGoal(
            date=datetime.now(),
            revenue_target=data.revenue_target,
            orders_target=data.orders_target
        )
        db.add(goal)
    
    db.commit()
    
    return {
        "message": "Goal set!",
        "revenue_target": data.revenue_target,
        "orders_target": data.orders_target
    }
