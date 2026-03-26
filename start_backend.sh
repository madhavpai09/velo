#!/bin/bash
# Start the Mini Uber Backend Server

echo "📦 Installing dependencies..."
pip install -q -r serverapp/requirements.txt

echo "✅ Starting Backend Server..."
cd serverapp
python3 -m uvicorn server:app --reload --host 0.0.0.0 --port 8000

