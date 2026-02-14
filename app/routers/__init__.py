from .menu import router as menu_router
from .orders import router as orders_router
from .payments import router as payments_router
from .locations import router as locations_router
from .ingredients import router as ingredients_router
from .sales import router as sales_router
from .modifiers import router as modifiers_router
from .kitchen import router as kitchen_router
from .shifts import router as shifts_router
from .receipts import router as receipts_router
from .history import router as history_router
from .discounts import router as discounts_router
from .export import router as export_router
from .refunds import router as refunds_router
from .settings import router as settings_router
from .feedback import router as feedback_router
from .prep import router as prep_router
from .weather import router as weather_router
from .customers import router as customers_router
from .catering import router as catering_router
from .promos import router as promos_router
from .events import router as events_router
from .reports import router as reports_router
from .goals import router as goals_router
from .voice import router as voice_router
from .favorites import router as favorites_router
from .schedule import router as schedule_router
from .trucks import router as trucks_router
from .offline import router as offline_router

__all__ = [
    "menu_router",
    "orders_router",
    "payments_router",
    "locations_router",
    "ingredients_router",
    "sales_router",
    "modifiers_router",
    "kitchen_router",
    "shifts_router",
    "receipts_router",
    "history_router",
    "discounts_router",
    "export_router",
    "refunds_router",
    "settings_router",
    "feedback_router",
    "prep_router",
    "weather_router",
    "customers_router",
    "catering_router",
    "promos_router",
    "events_router",
    "reports_router",
    "goals_router",
    "voice_router",
    "favorites_router",
    "schedule_router",
    "trucks_router",
    "offline_router"
]
