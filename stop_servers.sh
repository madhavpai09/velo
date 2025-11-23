#!/bin/bash

echo "🛑 Stopping all Mini Uber servers..."

lsof -ti:8000 | xargs kill -9 2>/dev/null && echo "✅ Stopped server on port 8000"
lsof -ti:8001 | xargs kill -9 2>/dev/null && echo "✅ Stopped server on port 8001"
lsof -ti:8002 | xargs kill -9 2>/dev/null && echo "✅ Stopped server on port 8002"

echo ""
echo "✅ All servers stopped!"
