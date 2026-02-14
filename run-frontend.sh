#!/bin/bash
# Start Food Truck POS frontend
cd "$(dirname "$0")/frontend"
npm run dev -- --port 3007
