# Food Truck POS

A fast, mobile-first point-of-sale system designed specifically for food trucks.

## Features

- 🚀 **Quick-tap menu items** - Speed is critical in food service
- 🔴 **Item availability toggle** - Mark items as sold out instantly
- 📍 **Location tracking / event mode** - Track sales by location
- 💵 **Simple cash + card payment** - Fast checkout
- 📴 **Offline-capable design** - Works without internet
- 📊 **Daily sales summary** - Know your numbers
- 🥬 **Ingredient inventory** - Simple tracking mode
- 📋 **Customer queue display** - Show order progress
- 📱 **Mobile-first responsive design** - Works on any device

## Quick Start

### Backend
```bash
cd ~/food-truck-pos
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```

### Frontend
```bash
cd ~/food-truck-pos/frontend
npm install
npm run dev -- --port 3007
```

## API Endpoints

- `GET /` - API info
- `GET /health` - Health check
- `GET /menu` - List menu items
- `POST /orders` - Create order
- `GET /orders/{id}` - Get order
- `PATCH /orders/{id}/status` - Update order status
- `GET /queue` - Customer queue display
- `GET /sales/daily` - Daily sales summary
- `POST /payments` - Process payment

## Tech Stack

- **Backend**: FastAPI + SQLite
- **Frontend**: React + Vite + Tailwind CSS
