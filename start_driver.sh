#!/bin/bash

# Mini Uber - Start Driver Client
# Usage: ./start_driver.sh [port] [driver_id]

PORT=${1:-9000}
DRIVER_ID=${2:-""}

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/client"

echo "🚗 Starting Driver Client on port $PORT..."

if [ -z "$DRIVER_ID" ]; then
    python3 driver_client.py --port $PORT
else
    python3 driver_client.py --port $PORT --driver-id "$DRIVER_ID"
fi

