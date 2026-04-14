"""
User management routes: /users, /create-user
Handles listing all users and creating new ones.
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from backend.models import database as db

router = APIRouter()
templates = Jinja2Templates(directory="backend/templates")


def require_auth(request: Request):
    """Simple auth guard — returns True if authenticated."""
    return request.cookies.get("session") == "authenticated"


# ---------------------------------------------------------------------------
# GET /users — list all users
# ---------------------------------------------------------------------------
@router.get("/users", response_class=HTMLResponse)
async def list_users(request: Request):
    """Display all users in a table view."""
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=302)

    users = db.get_all_users()
    return templates.TemplateResponse(
        "users.html",
        {"request": request, "users": users, "message": None, "error": None},
    )


# ---------------------------------------------------------------------------
# GET /create-user — show the create user form
# ---------------------------------------------------------------------------
@router.get("/create-user", response_class=HTMLResponse)
async def create_user_form(request: Request):
    """Render the create user form."""
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        "create_user.html",
        {
            "request": request,
            "message": None,
            "error": None,
            "license_types": db.LICENSE_TYPES,
        },
    )


# ---------------------------------------------------------------------------
# POST /create-user — handle form submission
# ---------------------------------------------------------------------------
@router.post("/create-user", response_class=HTMLResponse)
async def create_user_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    license_type: str = Form("basic"),
):
    """Process user creation form."""
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=302)

    try:
        user = db.create_user(name=name, email=email, password=password, license_type=license_type)
        return templates.TemplateResponse(
            "create_user.html",
            {
                "request": request,
                "message": f"✅ User '{user['name']}' ({user['email']}) created successfully!",
                "error": None,
                "license_types": db.LICENSE_TYPES,
            },
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "create_user.html",
            {
                "request": request,
                "message": None,
                "error": f"❌ Error: {str(e)}",
                "license_types": db.LICENSE_TYPES,
            },
            status_code=400,
        )
