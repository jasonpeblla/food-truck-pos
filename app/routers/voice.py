from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/voice", tags=["voice"])

class Announcement(BaseModel):
    text: str
    order_number: int = 0

@router.get("/order-ready/{order_number}")
def get_order_ready_announcement(order_number: int, customer_name: str = ""):
    """Get text for order ready announcement."""
    if customer_name:
        text = f"Order number {order_number} for {customer_name} is ready for pickup!"
    else:
        text = f"Order number {order_number} is now ready for pickup!"
    
    return {
        "text": text,
        "ssml": f'<speak><prosody rate="medium" pitch="medium">{text}</prosody></speak>',
        "order_number": order_number
    }

@router.get("/queue-status")
def get_queue_announcement(preparing: List[int] = [], ready: List[int] = []):
    """Get queue status announcement."""
    parts = []
    
    if ready:
        if len(ready) == 1:
            parts.append(f"Order {ready[0]} is ready for pickup.")
        else:
            parts.append(f"Orders {', '.join(map(str, ready[:-1])) + ' and ' + str(ready[-1])} are ready for pickup.")
    
    if preparing:
        if len(preparing) == 1:
            parts.append(f"Order {preparing[0]} is being prepared.")
        else:
            parts.append(f"Orders {', '.join(map(str, preparing))} are being prepared.")
    
    text = " ".join(parts) if parts else "No orders in queue."
    
    return {
        "text": text,
        "ready_count": len(ready),
        "preparing_count": len(preparing)
    }

@router.get("/daily-special")
def get_daily_special_announcement(item_name: str, price: float):
    """Announcement for daily special."""
    text = f"Try our daily special! {item_name} for only ${price:.2f}!"
    
    return {
        "text": text,
        "item": item_name,
        "price": price
    }
