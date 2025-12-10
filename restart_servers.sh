#!/bin/bash
# Quick fix script to restart the backend server with new admin routes

echo "🔄 Restarting VELO Cabs Backend Server..."
echo ""

# Kill existing server processes
echo "Stopping existing servers..."
pkill -f "python.*server.py" 2>/dev/null
pkill -f "python.*server_matcher.py" 2>/dev/null
pkill -f "python.*server_notifier.py" 2>/dev/null

sleep 2

# Navigate to serverapp directory
cd "$(dirname "$0")/serverapp" || exit 1

# Start servers in background
echo "Starting main server..."
.venv/bin/python server.py &

sleep 2

echo "Starting matcher service..."
.venv/bin/python server_matcher.py &

sleep 1

echo "Starting notifier service..."
.venv/bin/python server_notifier.py &

sleep 2

echo ""
echo "✅ All servers restarted!"
echo ""
echo "Testing admin endpoint..."
sleep 1
curl -s http://localhost:8000/api/admin/drivers | head -100
echo ""
echo ""
echo "If you see driver data above, the admin API is working!"
echo "Navigate to http://localhost:5173/admin to use the admin dashboard"
