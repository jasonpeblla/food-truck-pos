from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Optional

from app.database import get_db, Base

router = APIRouter(prefix="/events", tags=["events"])

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    event_type = Column(String, default="festival")  # festival, market, private, popup
    location = Column(String, default="")
    address = Column(String, default="")
    date = Column(DateTime, nullable=False)
    start_time = Column(String, default="11:00")
    end_time = Column(String, default="20:00")
    expected_customers = Column(Integer, default=100)
    booth_fee = Column(Float, default=0.0)
    notes = Column(Text, default="")
    status = Column(String, default="upcoming")  # upcoming, active, completed
    actual_revenue = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class EventCreate(BaseModel):
    name: str
    event_type: str = "festival"
    location: str = ""
    address: str = ""
    date: str  # ISO date
    start_time: str = "11:00"
    end_time: str = "20:00"
    expected_customers: int = 100
    booth_fee: float = 0.0
    notes: str = ""

@router.post("")
def create_event(data: EventCreate, db: Session = Depends(get_db)):
    event = Event(
        name=data.name,
        event_type=data.event_type,
        location=data.location,
        address=data.address,
        date=datetime.strptime(data.date, "%Y-%m-%d"),
        start_time=data.start_time,
        end_time=data.end_time,
        expected_customers=data.expected_customers,
        booth_fee=data.booth_fee,
        notes=data.notes
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

@router.get("")
def get_events(upcoming_only: bool = True, db: Session = Depends(get_db)):
    query = db.query(Event)
    if upcoming_only:
        query = query.filter(Event.date >= datetime.now())
    return query.order_by(Event.date).all()

@router.get("/today")
def get_today_event(db: Session = Depends(get_db)):
    today = date.today()
    event = db.query(Event).filter(
        Event.date >= datetime(today.year, today.month, today.day),
        Event.date < datetime(today.year, today.month, today.day + 1)
    ).first()
    return event

@router.patch("/{event_id}/status")
def update_event_status(event_id: int, status: str, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.status = status
    db.commit()
    return {"status": status}

@router.patch("/{event_id}/revenue")
def update_event_revenue(event_id: int, revenue: float, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.actual_revenue = revenue
    db.commit()
    return {"revenue": revenue}
