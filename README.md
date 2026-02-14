# 🌮 Food Truck POS

A fast, mobile-first point-of-sale system designed specifically for food trucks.

## Features

### Core POS
- 🚀 **Quick-tap menu items** - Speed is critical in food service
- 🔴 **Item availability toggle** - Mark items as sold out instantly
- 🛒 **Fast cart management** - Add, remove, adjust quantities
- 💵 **Simple cash + card payment** - With tip support and change calculation
- 📋 **Customer name tracking** - Optional for order identification

### Kitchen & Operations
- 👨‍🍳 **Kitchen Display System** - Real-time order view with bump functionality
- 📺 **Customer Queue Display** - Show order progress to customers
- ⏱️ **Order timing** - Track prep time, flag slow orders
- 🔔 **Sound notifications** - Audio alerts for new orders

### Business Management
- 📊 **Daily sales summary** - Know your numbers at a glance
- 📈 **Weekly reports** - Track trends and performance
- ⏰ **Hourly breakdown** - Find your peak hours
- 🏆 **Top items tracking** - Know what sells

### Advanced Features
- 📍 **Location tracking** - Track sales by location/event
- 🎫 **Discount codes** - Percent or fixed amount discounts
- 🧾 **Receipt generation** - Text receipts for printing
- 💰 **Shift management** - Track drawer and staff
- 📦 **Data export** - CSV export for orders, sales, menu
- 🥬 **Ingredient inventory** - Simple stock tracking
- 🔧 **Modifiers** - Customize menu items

### Technical
- 📴 **Offline-capable** - PWA with service worker
- 📱 **Mobile-first design** - Works great on tablets and phones
- 🌐 **WebSocket support** - Real-time kitchen updates
- 🔄 **Auto-refresh** - Orders update automatically

## Quick Start

### Backend
```bash
cd ~/food-truck-pos
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./run.sh
```

### Frontend
```bash
cd ~/food-truck-pos/frontend
npm install
npm run dev -- --port 3007
```

Access the POS at: http://localhost:3007

## API Endpoints

### Menu
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/menu` | List all menu items |
| POST | `/menu` | Create menu item |
| PATCH | `/menu/{id}` | Update menu item |
| PATCH | `/menu/{id}/toggle-availability` | Toggle sold out |

### Orders
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/orders` | Get today's orders |
| POST | `/orders` | Create new order |
| GET | `/orders/queue` | Get queue display |
| PATCH | `/orders/{id}/status` | Update status |

### Payments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/payments` | Process payment |
| GET | `/payments` | List payments |

### Kitchen
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/kitchen/orders` | Get kitchen orders |
| POST | `/kitchen/bump/{id}` | Bump order status |
| WS | `/kitchen/ws` | WebSocket for real-time |

### Sales & Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/sales/daily` | Daily summary |
| GET | `/sales/weekly` | Weekly summary |
| GET | `/sales/hourly` | Hourly breakdown |
| GET | `/history/stats` | Period statistics |

### Shifts
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/shifts/start` | Start shift |
| POST | `/shifts/close` | Close shift |
| GET | `/shifts/active` | Get active shift |

### Export
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/export/orders/csv` | Export orders |
| GET | `/export/sales/csv` | Export sales |
| GET | `/export/menu/csv` | Export menu |

## Tech Stack

- **Backend**: FastAPI + SQLite + SQLAlchemy
- **Frontend**: React + Vite + Tailwind CSS + TypeScript
- **Real-time**: WebSocket

## Configuration

### Tax Rate
Edit `app/routers/orders.py`:
```python
TAX_RATE = 0.0875  # 8.75%
```

### Default Menu
Edit `app/main.py` to customize the seed menu.

## Screenshots

The POS features a dark theme optimized for outdoor/variable lighting conditions typical of food truck operations.

### Views
- **POS** - Main ordering interface with quick-tap menu
- **Orders** - Active order management
- **Kitchen** - Kitchen display system
- **Queue** - Customer-facing order status
- **Sales** - Daily reports and analytics
- **Menu** - Toggle item availability

## License

MIT
