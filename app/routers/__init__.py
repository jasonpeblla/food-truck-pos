from .menu import router as menu_router
from .orders import router as orders_router
from .payments import router as payments_router
from .locations import router as locations_router
from .ingredients import router as ingredients_router
from .sales import router as sales_router

__all__ = [
    "menu_router",
    "orders_router",
    "payments_router",
    "locations_router",
    "ingredients_router",
    "sales_router"
]
