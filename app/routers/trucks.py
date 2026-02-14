from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.database import get_db, Base

router = APIRouter(prefix="/trucks", tags=["trucks"])

class Truck(Base):
    __tablename__ = "trucks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    plate_number = Column(String, default="")
    current_location = Column(String, default="")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    status = Column(String, default="idle")  # idle, en_route, serving, closed
    current_event = Column(String, default="")
    last_checkin = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class TruckCreate(BaseModel):
    name: str
    plate_number: str = ""

class TruckCheckin(BaseModel):
    location: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: str = "serving"
    event: str = ""

@router.post("")
def create_truck(data: TruckCreate, db: Session = Depends(get_db)):
    """Register a new truck."""
    truck = Truck(name=data.name, plate_number=data.plate_number)
    db.add(truck)
    db.commit()
    db.refresh(truck)
    return truck

@router.get("")
def get_trucks(active_only: bool = True, db: Session = Depends(get_db)):
    """Get all trucks."""
    query = db.query(Truck)
    if active_only:
        query = query.filter(Truck.is_active == True)
    return query.all()

@router.get("/{truck_id}")
def get_truck(truck_id: int, db: Session = Depends(get_db)):
    """Get a specific truck."""
    truck = db.query(Truck).filter(Truck.id == truck_id).first()
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    return truck

@router.post("/{truck_id}/checkin")
def truck_checkin(truck_id: int, data: TruckCheckin, db: Session = Depends(get_db)):
    """Check in truck at a location."""
    truck = db.query(Truck).filter(Truck.id == truck_id).first()
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    
    truck.current_location = data.location
    truck.latitude = data.latitude
    truck.longitude = data.longitude
    truck.status = data.status
    truck.current_event = data.event
    truck.last_checkin = datetime.utcnow()
    
    db.commit()
    return {"checkin": "success", "truck": truck.name, "location": data.location}

@router.get("/map/all")
def get_truck_map(db: Session = Depends(get_db)):
    """Get all active trucks with locations for map display."""
    trucks = db.query(Truck).filter(
        Truck.is_active == True,
        Truck.status.in_(['serving', 'en_route'])
    ).all()
    
    return [{
        "id": t.id,
        "name": t.name,
        "location": t.current_location,
        "lat": t.latitude,
        "lng": t.longitude,
        "status": t.status,
        "event": t.current_event,
        "last_checkin": t.last_checkin.isoformat() if t.last_checkin else None
    } for t in trucks]

@router.patch("/{truck_id}/status")
def update_truck_status(truck_id: int, status: str, db: Session = Depends(get_db)):
    """Update truck status."""
    truck = db.query(Truck).filter(Truck.id == truck_id).first()
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    
    valid = ["idle", "en_route", "serving", "closed"]
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Use: {valid}")
    
    truck.status = status
    truck.last_checkin = datetime.utcnow()
    db.commit()
    
    return {"status": status}
