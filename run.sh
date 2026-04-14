#!/bin/bash
# ============================================================
# run.sh — Start the Agentic AI IT Support System
# ============================================================
# Usage:
#   ./run.sh                  # Start backend only
#   ./run.sh agent "reset password for john@company.com"

set -e  # Exit on error

echo "============================================================"
echo "  Agentic AI IT Support Automation System"
echo "============================================================"

# ---- Check Python ----
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

# ---- Check .env ----
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Copying .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env and add your GROQ_API_KEY, then re-run."
    exit 1
fi

# ---- Install dependencies if needed ----
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

echo "📦 Installing dependencies..."
pip install -r requirements.txt -q

# ---- Install Playwright browsers ----
if [ ! -d "$HOME/.cache/ms-playwright" ] && [ ! -d "$LOCALAPPDATA/ms-playwright" ]; then
    echo "🌐 Installing Playwright browsers (first time)..."
    playwright install chromium
fi

# ---- Start backend or run agent ----
if [ "$1" == "agent" ]; then
    # Run agent with provided request
    shift
    echo "🤖 Running agent: $*"
    python run_agent.py "$@"
else
    # Start backend server
    echo ""
    echo "🚀 Starting Mock IT Admin Panel..."
    echo "   URL: http://localhost:8000"
    echo "   Login: admin / admin123"
    echo ""
    echo "To run the agent (in another terminal):"
    echo '   python run_agent.py "reset password for john@company.com"'
    echo ""
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
fi
