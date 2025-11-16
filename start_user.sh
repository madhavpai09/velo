#!/bin/bash

# Mini Uber - Start User Client
# Usage: ./start_user.sh [port] [from_location] [to_location]

PORT=${1:-6000}
FROM=${2:-"123 Main St, Chennai"}
TO=${3:-"456 Park Ave, Chennai"}

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/client"

echo "👤 Starting User Client on port $PORT..."
echo "   From: $FROM"
echo "   To: $TO"

python3 user_client.py --port $PORT --from "$FROM" --to "$TO"

