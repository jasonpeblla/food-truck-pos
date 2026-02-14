from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Location
from app.schemas import LocationCreate, LocationResponse, LocationUpdate

router = APIRouter(prefix="/locations", tags=["locations"])

@router.get("", response_model=List[LocationResponse])
def get_locations(db: Session = Depends(get_db)):
    """Get all locations."""
    return db.query(Location).order_by(Location.name).all()

@router.get("/active", response_model=LocationResponse)
def get_active_location(db: Session = Depends(get_db)):
    """Get the currently active location."""
    location = db.query(Location).filter(Location.is_active == True).first()
    if not location:
        raise HTTPException(status_code=404, detail="No active location")
    return location

@router.get("/{location_id}", response_model=LocationResponse)
def get_location(location_id: int, db: Session = Depends(get_db)):
    """Get a specific location."""
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location

@router.post("", response_model=LocationResponse)
def create_location(location_data: LocationCreate, db: Session = Depends(get_db)):
    """Create a new location."""
    location = Location(**location_data.model_dump())
    db.add(location)
    db.commit()
    db.refresh(location)
    return location

@router.patch("/{location_id}", response_model=LocationResponse)
def update_location(location_id: int, update: LocationUpdate, db: Session = Depends(get_db)):
    """Update a location."""
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(location, key, value)
    
    db.commit()
    db.refresh(location)
    return location

@router.post("/{location_id}/activate", response_model=LocationResponse)
def activate_location(location_id: int, db: Session = Depends(get_db)):
    """Set a location as active (deactivates all others)."""
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Deactivate all locations
    db.query(Location).update({Location.is_active: False})
    
    # Activate this one
    location.is_active = True
    db.commit()
    db.refresh(location)
    return location

@router.delete("/{location_id}")
def delete_location(location_id: int, db: Session = Depends(get_db)):
    """Delete a location."""
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    db.delete(location)
    db.commit()
    return {"message": "Location deleted"}
