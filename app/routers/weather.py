from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import random

from app.database import get_db
from app.models import MenuItem

router = APIRouter(prefix="/weather", tags=["weather"])

# Weather-based menu recommendations
# Maps weather conditions to preferred menu categories/attributes
WEATHER_PREFERENCES = {
    "hot": {
        "boost": ["drinks", "sides"],  # Cold drinks, lighter items
        "emoji_boost": ["🥤", "🍦", "🥗", "🌮"],  # Lighter fare
        "description": "Hot weather - recommending refreshing items"
    },
    "cold": {
        "boost": ["mains", "specials"],  # Heartier, warm items
        "emoji_boost": ["🍜", "🌯", "🍲"],  # Warm/hearty items
        "description": "Cold weather - recommending warm, hearty items"
    },
    "rainy": {
        "boost": ["mains", "specials"],  # Comfort food
        "emoji_boost": ["🌯", "🍲", "🌮"],  # Comfort items
        "description": "Rainy day - recommending comfort food"
    },
    "nice": {
        "boost": [],  # No particular boost
        "emoji_boost": [],
        "description": "Nice weather - all items recommended"
    }
}

def classify_weather(temp_f: float, condition: str = "clear") -> str:
    """Classify weather into simple categories."""
    condition = condition.lower()
    
    if "rain" in condition or "storm" in condition or "drizzle" in condition:
        return "rainy"
    elif temp_f >= 85:
        return "hot"
    elif temp_f <= 50:
        return "cold"
    else:
        return "nice"

@router.get("/recommendations")
def get_weather_recommendations(
    temp_f: float = 72,
    condition: str = "clear",
    db: Session = Depends(get_db)
):
    """
    Get menu recommendations based on weather.
    In production, this would integrate with a weather API.
    For now, accepts temp and condition as parameters.
    """
    weather_type = classify_weather(temp_f, condition)
    prefs = WEATHER_PREFERENCES[weather_type]
    
    # Get available menu items
    items = db.query(MenuItem).filter(MenuItem.is_available == True).all()
    
    # Score items based on weather
    recommendations = []
    for item in items:
        score = 50  # Base score
        
        # Boost by category
        if item.category.lower() in [c.lower() for c in prefs["boost"]]:
            score += 30
        
        # Boost by emoji (proxy for item type)
        if item.emoji in prefs["emoji_boost"]:
            score += 20
        
        # Add some randomness
        score += random.randint(0, 10)
        
        recommendations.append({
            "id": item.id,
            "name": item.name,
            "emoji": item.emoji,
            "price": item.price,
            "category": item.category,
            "score": score
        })
    
    # Sort by score, return top 5
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "weather_type": weather_type,
        "description": prefs["description"],
        "temp_f": temp_f,
        "condition": condition,
        "recommended_items": recommendations[:5]
    }

@router.get("/current")
def get_current_weather():
    """
    Get current weather (mock implementation).
    In production, integrate with OpenWeatherMap or similar.
    Returns mock data based on time of day for demo.
    """
    from datetime import datetime
    hour = datetime.now().hour
    
    # Mock weather based on time
    if 6 <= hour < 10:
        return {"temp_f": 62, "condition": "clear", "description": "Cool morning"}
    elif 10 <= hour < 14:
        return {"temp_f": 78, "condition": "sunny", "description": "Warm midday"}
    elif 14 <= hour < 18:
        return {"temp_f": 85, "condition": "sunny", "description": "Hot afternoon"}
    elif 18 <= hour < 21:
        return {"temp_f": 72, "condition": "clear", "description": "Pleasant evening"}
    else:
        return {"temp_f": 58, "condition": "clear", "description": "Cool night"}
