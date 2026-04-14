"""
Authentication routes: /login, /logout
Uses cookie-based session to track the logged-in admin.
"""

from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from backend.models.database import ADMIN_USERNAME, ADMIN_PASSWORD

router = APIRouter()
templates = Jinja2Templates(directory="backend/templates")

# ---------------------------------------------------------------------------
# GET /login — render the login form
# ---------------------------------------------------------------------------
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Show the admin login page."""
    # If already logged in, redirect to dashboard
    if request.cookies.get("session") == "authenticated":
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


# ---------------------------------------------------------------------------
# POST /login — handle login form submission
# ---------------------------------------------------------------------------
@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    """Validate credentials and set session cookie."""
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        response = RedirectResponse(url="/dashboard", status_code=302)
        # Simple cookie-based session (not for production)
        response.set_cookie(key="session", value="authenticated", httponly=True)
        return response

    # Wrong credentials — re-render with error
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Invalid username or password."},
        status_code=401,
    )


# ---------------------------------------------------------------------------
# GET /logout — clear session and redirect to login
# ---------------------------------------------------------------------------
@router.get("/logout")
async def logout():
    """Destroy session cookie and redirect to login."""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session")
    return response
