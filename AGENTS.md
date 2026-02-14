# AGENTS.md - Food Truck POS Workspace

## Repository

- **GitHub:** https://github.com/jasonpeblla/food-truck-pos
- **Local:** `~/food-truck-pos/`
- **Backend Port:** 8005
- **Frontend Port:** 3007

## POS Control

The Food Truck POS runs at `http://localhost:8005`. Use curl to interact with it.

### Menu Operations
```bash
# Get all menu items
curl http://localhost:8005/menu

# Get available items only
curl "http://localhost:8005/menu?available_only=true"

# Get menu categories
curl http://localhost:8005/menu/categories

# Create menu item
curl -X POST http://localhost:8005/menu \
  -H "Content-Type: application/json" \
  -d '{"name": "New Taco", "category": "tacos", "price": 4.50, "emoji": "🌮"}'

# Toggle item availability (sold out)
curl -X PATCH http://localhost:8005/menu/1/toggle-availability
```

### Order Operations
```bash
# Create order
curl -X POST http://localhost:8005/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_name": "John", "items": [{"menu_item_id": 1, "quantity": 2}]}'

# Get today's orders
curl http://localhost:8005/orders

# Get order queue (for customer display)
curl http://localhost:8005/orders/queue

# Update order status
curl -X PATCH http://localhost:8005/orders/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "preparing"}'
```

### Payment Operations
```bash
# Process cash payment
curl -X POST http://localhost:8005/payments \
  -H "Content-Type: application/json" \
  -d '{"order_id": 1, "amount": 10.00, "method": "cash", "tip": 2.00, "cash_tendered": 15.00}'

# Process card payment
curl -X POST http://localhost:8005/payments \
  -H "Content-Type: application/json" \
  -d '{"order_id": 1, "amount": 10.00, "method": "card", "tip": 2.00}'
```

### Kitchen Operations
```bash
# Get kitchen orders
curl http://localhost:8005/kitchen/orders

# Bump order to next status
curl -X POST http://localhost:8005/kitchen/bump/1
```

### Sales & Reports
```bash
# Get daily sales
curl http://localhost:8005/sales/daily

# Get weekly sales
curl http://localhost:8005/sales/weekly

# Get hourly breakdown
curl http://localhost:8005/sales/hourly

# Get stats for last 7 days
curl http://localhost:8005/history/stats?days=7
```

### Shift Management
```bash
# Start shift
curl -X POST http://localhost:8005/shifts/start \
  -H "Content-Type: application/json" \
  -d '{"staff_name": "John", "starting_cash": 100.00}'

# Get active shift
curl http://localhost:8005/shifts/active

# Close shift
curl -X POST http://localhost:8005/shifts/close \
  -H "Content-Type: application/json" \
  -d '{"ending_cash": 350.00, "notes": "Good day!"}'
```

### Discounts
```bash
# Create discount
curl -X POST http://localhost:8005/discounts \
  -H "Content-Type: application/json" \
  -d '{"code": "TACO10", "discount_type": "percent", "amount": 10}'

# Validate discount
curl "http://localhost:8005/discounts/validate/TACO10?order_total=20.00"
```

### Data Export
```bash
# Export orders CSV
curl http://localhost:8005/export/orders/csv > orders.csv

# Export menu CSV
curl http://localhost:8005/export/menu/csv > menu.csv

# Export all data as JSON
curl http://localhost:8005/export/json
```

### Receipts
```bash
# Get receipt data
curl http://localhost:8005/receipts/1

# Get printable text receipt
curl http://localhost:8005/receipts/1/text
```

## Service Control

```bash
# Start backend
cd ~/food-truck-pos && ./run.sh

# Start frontend
cd ~/food-truck-pos && ./run-frontend.sh

# Or manually:
cd ~/food-truck-pos && source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload

cd ~/food-truck-pos/frontend && npm run dev -- --port 3007
```

## Memory

Write daily notes to `memory/YYYY-MM-DD.md` for context between sessions.
