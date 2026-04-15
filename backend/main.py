"""
Mock IT Admin Panel — FastAPI Application Entry Point
-----------------------------------------------------
This is the web application that the AI agent will interact with
via browser automation (Playwright). It simulates a real IT admin
panel with login, user management, and admin operations.
"""

import os
import sys
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from backend.routes.auth import router as auth_router
from backend.routes.users import router as users_router
from backend.routes.admin import router as admin_router

# Check for required environment variables EARLY
try:
    from backend.routes.automation import router as automation_router
except Exception as e:
    print(f"⚠️  Warning: Could not load automation router: {e}", file=sys.stderr)
    automation_router = None

# ---------------------------------------------------------------------------
# Create FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Mock IT Admin Panel",
    description="A simulated IT admin panel for the Agentic AI automation demo",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Health check endpoint (no auth required)
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    """Simple health check - verifies app is running."""
    return {
        "status": "ok",
        "message": "Mock IT Admin Panel is running!",
        "login_url": "/login",
        "dashboard": "/dashboard"
    }

# ---------------------------------------------------------------------------
# Register route modules
# ---------------------------------------------------------------------------
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(admin_router)
if automation_router:
    app.include_router(automation_router)

# ---------------------------------------------------------------------------
# Mount static files (CSS, JS, images)
# ---------------------------------------------------------------------------
# Optional: Mount static directory if you add it later
# app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# ---------------------------------------------------------------------------
# Startup message
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    print("=" * 70)
    print("  ✅ Mock IT Admin Panel is running!")
    print("=" * 70)
    print("  📍 URL: http://localhost:8000")
    print("  🔐 Login: admin / admin123")
    print("  📋 Routes:")
    print("     • /login              → Admin login")
    print("     • /dashboard          → Admin dashboard")
    print("     • /users              → User management")
    print("     • /create-user        → Create new user")
    print("     • /reset-password     → Reset user password")
    print("     • /assign-license     → Assign licenses")
    print("     • /automation         → 🤖 Real-time task automation")
    print("=" * 70)
    
    # Check for GROQ_API_KEY in production
    if not os.getenv("GROQ_API_KEY"):
        print("  ⚠️  WARNING: GROQ_API_KEY environment variable not found!")
        print("     Automation tasks will fail. Set this in Railway Variables:")
        print("     1. Go to Railway dashboard → Variables tab")
        print("     2. Add: GROQ_API_KEY = your_key_from_console.groq.com")
        print("     3. Click Redeploy")
        print("=" * 70)
    
    if automation_router:
        print("  ✅ Automation router loaded successfully")
    else:
        print("  ⚠️  Automation router failed to load")
    
    print("=" * 70 + "\n")


# ---------------------------------------------------------------------------
# Run directly (for development)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
