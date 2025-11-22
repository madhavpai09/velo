#!/bin/bash

# Mini Uber - Start All Server Services
# This script starts all 3 server services in separate terminal windows

echo "🚀 Starting Mini Uber Server Services..."
echo ""

# Get the project directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/serverapp"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Check for virtual environment
PYTHON_CMD="python3"
if [ -f "$SCRIPT_DIR/serverapp/.venv/bin/python" ]; then
    PYTHON_CMD="$SCRIPT_DIR/serverapp/.venv/bin/python"
    echo "✅ Using virtual environment: $PYTHON_CMD"
else
    echo "⚠️  Virtual environment not found, using system python3"
fi

# Function to start a service in a new terminal window
start_service() {
    local service_name=$1
    local script_name=$2
    local port=$3
    
    echo "📡 Starting $service_name on port $port..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR/serverapp' && '$PYTHON_CMD' $script_name\""
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        gnome-terminal -- bash -c "cd '$SCRIPT_DIR/serverapp' && '$PYTHON_CMD' $script_name; exec bash" 2>/dev/null || \
        xterm -e "cd '$SCRIPT_DIR/serverapp' && '$PYTHON_CMD' $script_name" 2>/dev/null || \
        echo "⚠️  Could not open new terminal. Please run manually: cd serverapp && $PYTHON_CMD $script_name"
    else
        echo "⚠️  Unsupported OS. Please run manually: cd serverapp && $PYTHON_CMD $script_name"
    fi
    
    sleep 1
}

# Start all server services
start_service "Main Server" "server.py" "8000"
start_service "Matcher Service" "server_matcher.py" "8001"
start_service "Notifier Service" "server_notifier.py" "8002"

echo ""
echo "✅ All server services started!"
echo ""
echo "📋 Next steps:"
echo "   1. Start at least 1 driver: cd client && python3 driver_client.py --port 9000"
echo "   2. Start a user when ready: cd client && python3 user_client.py --port 6000"
echo ""

