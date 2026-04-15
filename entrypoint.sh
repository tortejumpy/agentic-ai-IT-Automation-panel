#!/bin/bash
# Railway Startup Script
# Handles proper environment variable expansion and starts Uvicorn

set -e

# Get the port from Railway's PORT environment variable, or default to 8000
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}

echo "=========================================="
echo "🚀 Starting Mock IT Admin Panel"
echo "=========================================="
echo "HOST: $HOST"
echo "PORT: $PORT"
echo "APP: backend.main:app"
echo "=========================================="

# Start Uvicorn with the proper port
exec uvicorn backend.main:app \
    --host $HOST \
    --port $PORT \
    --workers 1
