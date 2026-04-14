"""
Mock IT Admin Panel — FastAPI Application Entry Point
-----------------------------------------------------
This is the web application that the AI agent will interact with
via browser automation (Playwright). It simulates a real IT admin
panel with login, user management, and admin operations.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from backend.routes.auth import router as auth_router
from backend.routes.users import router as users_router
from backend.routes.admin import router as admin_router

# ---------------------------------------------------------------------------
# Create FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Mock IT Admin Panel",
    description="A simulated IT admin panel for the Agentic AI automation demo",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Register route modules
# ---------------------------------------------------------------------------
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(admin_router)

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
    print("=" * 60)
    print("  Mock IT Admin Panel is running!")
    print("  URL: http://localhost:8000")
    print("  Login: admin / admin123")
    print("  Routes: /login, /dashboard, /users, /create-user")
    print("          /reset-password, /assign-license")
    print("=" * 60)


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
