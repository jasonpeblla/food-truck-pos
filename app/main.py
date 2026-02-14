from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import engine, Base, SessionLocal
from app.routers import (
    menu_router,
    orders_router,
    payments_router,
    locations_router,
    ingredients_router,
    sales_router,
    modifiers_router,
    kitchen_router,
    shifts_router,
    receipts_router,
    history_router,
    discounts_router,
    export_router,
    refunds_router,
    settings_router
)
from app.models import MenuItem, Location

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Seed default menu items if none exist
    db = SessionLocal()
    try:
        if db.query(MenuItem).count() == 0:
            default_items = [
                # Tacos
                MenuItem(name="Carne Asada Taco", category="tacos", price=4.50, emoji="🌮", display_order=1),
                MenuItem(name="Carnitas Taco", category="tacos", price=4.00, emoji="🌮", display_order=2),
                MenuItem(name="Al Pastor Taco", category="tacos", price=4.25, emoji="🌮", display_order=3),
                MenuItem(name="Chicken Taco", category="tacos", price=3.75, emoji="🌮", display_order=4),
                MenuItem(name="Fish Taco", category="tacos", price=5.00, emoji="🐟", display_order=5),
                MenuItem(name="Veggie Taco", category="tacos", price=3.50, emoji="🥬", display_order=6),
                # Burritos
                MenuItem(name="Carne Asada Burrito", category="burritos", price=11.00, emoji="🌯", display_order=1),
                MenuItem(name="Carnitas Burrito", category="burritos", price=10.00, emoji="🌯", display_order=2),
                MenuItem(name="Chicken Burrito", category="burritos", price=9.50, emoji="🌯", display_order=3),
                # Sides
                MenuItem(name="Chips & Guac", category="sides", price=5.00, emoji="🥑", display_order=1),
                MenuItem(name="Chips & Salsa", category="sides", price=3.00, emoji="🫙", display_order=2),
                MenuItem(name="Rice & Beans", category="sides", price=4.00, emoji="🍚", display_order=3),
                MenuItem(name="Elote (Street Corn)", category="sides", price=4.50, emoji="🌽", display_order=4),
                # Drinks
                MenuItem(name="Horchata", category="drinks", price=3.50, emoji="🥛", display_order=1),
                MenuItem(name="Jamaica", category="drinks", price=3.50, emoji="🧃", display_order=2),
                MenuItem(name="Mexican Coke", category="drinks", price=3.00, emoji="🥤", display_order=3),
                MenuItem(name="Water", category="drinks", price=1.50, emoji="💧", display_order=4),
            ]
            for item in default_items:
                db.add(item)
            
            # Add default location
            db.add(Location(name="Home Base", address="Mobile", is_active=True))
            db.commit()
    finally:
        db.close()
    
    yield

app = FastAPI(
    title="Food Truck POS",
    description="Fast, mobile-first point-of-sale for food trucks",
    version="0.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(menu_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(locations_router)
app.include_router(ingredients_router)
app.include_router(sales_router)
app.include_router(modifiers_router)
app.include_router(kitchen_router)
app.include_router(shifts_router)
app.include_router(receipts_router)
app.include_router(history_router)
app.include_router(discounts_router)
app.include_router(export_router)
app.include_router(refunds_router)
app.include_router(settings_router)

@app.get("/")
def root():
    return {
        "name": "Food Truck POS",
        "version": "0.1.0",
        "status": "running",
        "features": [
            "Quick-tap menu",
            "Order queue",
            "Cash & card payments",
            "Location tracking",
            "Sales reports",
            "Ingredient inventory"
        ]
    }

@app.get("/health")
def health():
    return {"status": "healthy"}
