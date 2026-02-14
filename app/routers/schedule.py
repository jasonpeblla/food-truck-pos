from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Time, Boolean
from pydantic import BaseModel
from datetime import datetime, time
from typing import List, Optional

from app.database import get_db, Base
from app.models import MenuItem

router = APIRouter(prefix="/schedule", tags=["schedule"])

class MenuSchedule(Base):
    __tablename__ = "menu_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    menu_item_id = Column(Integer, nullable=False)
    day_of_week = Column(String, default="all")  # all, mon, tue, wed, thu, fri, sat, sun
    start_time = Column(String, default="00:00")  # HH:MM
    end_time = Column(String, default="23:59")
    is_active = Column(Boolean, default=True)

class ScheduleCreate(BaseModel):
    menu_item_id: int
    day_of_week: str = "all"
    start_time: str = "00:00"
    end_time: str = "23:59"

@router.post("")
def create_schedule(data: ScheduleCreate, db: Session = Depends(get_db)):
    """Create a time-based menu schedule."""
    schedule = MenuSchedule(
        menu_item_id=data.menu_item_id,
        day_of_week=data.day_of_week,
        start_time=data.start_time,
        end_time=data.end_time
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule

@router.get("")
def get_schedules(menu_item_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get all menu schedules."""
    query = db.query(MenuSchedule)
    if menu_item_id:
        query = query.filter(MenuSchedule.menu_item_id == menu_item_id)
    return query.all()

@router.get("/available-now")
def get_available_now(db: Session = Depends(get_db)):
    """Get items available right now based on schedules."""
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    day_map = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}
    current_day = day_map[now.weekday()]
    
    # Get all items
    items = db.query(MenuItem).filter(MenuItem.is_available == True).all()
    
    # Check schedules
    available = []
    for item in items:
        schedules = db.query(MenuSchedule).filter(
            MenuSchedule.menu_item_id == item.id,
            MenuSchedule.is_active == True
        ).all()
        
        # If no schedules, item is always available
        if not schedules:
            available.append(item)
            continue
        
        # Check if any schedule matches current time
        for sched in schedules:
            day_match = sched.day_of_week == "all" or sched.day_of_week == current_day
            time_match = sched.start_time <= current_time <= sched.end_time
            
            if day_match and time_match:
                available.append(item)
                break
    
    return [{
        "id": item.id,
        "name": item.name,
        "emoji": item.emoji,
        "price": item.price,
        "category": item.category
    } for item in available]

@router.delete("/{schedule_id}")
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """Delete a schedule."""
    schedule = db.query(MenuSchedule).filter(MenuSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.delete(schedule)
    db.commit()
    return {"deleted": True}

# Breakfast/Lunch/Dinner presets
@router.post("/preset/{preset}")
def apply_preset(preset: str, menu_item_ids: List[int], db: Session = Depends(get_db)):
    """Apply a time preset to multiple items."""
    presets = {
        "breakfast": ("06:00", "11:00"),
        "lunch": ("11:00", "15:00"),
        "dinner": ("17:00", "22:00"),
        "late_night": ("22:00", "02:00"),
        "all_day": ("00:00", "23:59")
    }
    
    if preset not in presets:
        raise HTTPException(status_code=400, detail=f"Invalid preset. Use: {list(presets.keys())}")
    
    start, end = presets[preset]
    
    for item_id in menu_item_ids:
        schedule = MenuSchedule(
            menu_item_id=item_id,
            start_time=start,
            end_time=end
        )
        db.add(schedule)
    
    db.commit()
    return {"preset": preset, "items": len(menu_item_ids), "times": f"{start} - {end}"}
