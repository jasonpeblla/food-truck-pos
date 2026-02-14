from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json
import os

from app.database import get_db

router = APIRouter(prefix="/settings", tags=["settings"])

# Settings file path
SETTINGS_FILE = "settings.json"

# Default settings
DEFAULT_SETTINGS = {
    "business_name": "Food Truck POS",
    "tax_rate": 0.0875,
    "currency_symbol": "$",
    "receipt_footer": "Thank you for your order!",
    "enable_tips": True,
    "tip_presets": [0, 1, 2, 3, 5],
    "order_number_reset": "daily",  # daily, never
    "sound_enabled": True,
    "theme": "dark"
}

def load_settings():
    """Load settings from file."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                saved = json.load(f)
                return {**DEFAULT_SETTINGS, **saved}
        except:
            pass
    return DEFAULT_SETTINGS.copy()

def save_settings(settings: dict):
    """Save settings to file."""
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

class SettingsUpdate(BaseModel):
    business_name: Optional[str] = None
    tax_rate: Optional[float] = None
    currency_symbol: Optional[str] = None
    receipt_footer: Optional[str] = None
    enable_tips: Optional[bool] = None
    tip_presets: Optional[list] = None
    order_number_reset: Optional[str] = None
    sound_enabled: Optional[bool] = None
    theme: Optional[str] = None

@router.get("")
def get_settings():
    """Get current settings."""
    return load_settings()

@router.patch("")
def update_settings(update: SettingsUpdate):
    """Update settings."""
    settings = load_settings()
    
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        settings[key] = value
    
    save_settings(settings)
    return settings

@router.post("/reset")
def reset_settings():
    """Reset all settings to defaults."""
    save_settings(DEFAULT_SETTINGS.copy())
    return DEFAULT_SETTINGS

@router.get("/tax-rate")
def get_tax_rate():
    """Get current tax rate (for quick access)."""
    settings = load_settings()
    return {"tax_rate": settings.get("tax_rate", 0.0875)}
