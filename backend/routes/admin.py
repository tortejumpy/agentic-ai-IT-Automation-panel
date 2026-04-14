"""
Admin action routes: /dashboard, /reset-password, /assign-license
These are the core IT admin operations that the AI agent will automate.
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from backend.models import database as db

router = APIRouter()
templates = Jinja2Templates(directory="backend/templates")


def require_auth(request: Request):
    """Simple auth guard."""
    return request.cookies.get("session") == "authenticated"


# ---------------------------------------------------------------------------
# GET / — redirect root to dashboard
# ---------------------------------------------------------------------------
@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=302)
    return RedirectResponse(url="/dashboard", status_code=302)


# ---------------------------------------------------------------------------
# GET /dashboard — main control panel
# ---------------------------------------------------------------------------
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Show the IT admin dashboard with stats overview."""
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=302)

    stats = db.get_stats()
    recent_users = db.get_all_users()[-5:]  # Last 5 users for the panel
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "stats": stats, "recent_users": recent_users},
    )


# ---------------------------------------------------------------------------
# GET /reset-password — show reset password form
# ---------------------------------------------------------------------------
@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_form(request: Request, email: str = None):
    """Render the reset password form, optionally pre-filling email."""
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        "reset_password.html",
        {"request": request, "message": None, "error": None, "prefill_email": email or ""},
    )


# ---------------------------------------------------------------------------
# POST /reset-password — handle password reset submission
# ---------------------------------------------------------------------------
@router.post("/reset-password", response_class=HTMLResponse)
async def reset_password_submit(
    request: Request,
    email: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
):
    """Execute the password reset operation."""
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=302)

    # Validate password match
    if new_password != confirm_password:
        return templates.TemplateResponse(
            "reset_password.html",
            {
                "request": request,
                "message": None,
                "error": "❌ Passwords do not match.",
                "prefill_email": email,
            },
            status_code=400,
        )

    # Validate password length
    if len(new_password) < 6:
        return templates.TemplateResponse(
            "reset_password.html",
            {
                "request": request,
                "message": None,
                "error": "❌ Password must be at least 6 characters.",
                "prefill_email": email,
            },
            status_code=400,
        )

    success = db.reset_password(email=email, new_password=new_password)
    if success:
        return templates.TemplateResponse(
            "reset_password.html",
            {
                "request": request,
                "message": f"✅ Password for '{email}' has been reset successfully!",
                "error": None,
                "prefill_email": "",
            },
        )
    else:
        return templates.TemplateResponse(
            "reset_password.html",
            {
                "request": request,
                "message": None,
                "error": f"❌ User '{email}' not found.",
                "prefill_email": email,
            },
            status_code=404,
        )


# ---------------------------------------------------------------------------
# GET /assign-license — show license assignment form
# ---------------------------------------------------------------------------
@router.get("/assign-license", response_class=HTMLResponse)
async def assign_license_form(request: Request, email: str = None):
    """Render the assign license form, optionally pre-filling email."""
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        "assign_license.html",
        {
            "request": request,
            "message": None,
            "error": None,
            "license_types": db.LICENSE_TYPES,
            "prefill_email": email or "",
        },
    )


# ---------------------------------------------------------------------------
# POST /assign-license — handle license assignment
# ---------------------------------------------------------------------------
@router.post("/assign-license", response_class=HTMLResponse)
async def assign_license_submit(
    request: Request,
    email: str = Form(...),
    license_type: str = Form(...),
):
    """Execute the license assignment operation."""
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=302)

    success = db.assign_license(email=email, license_type=license_type)
    if success:
        return templates.TemplateResponse(
            "assign_license.html",
            {
                "request": request,
                "message": f"✅ License '{license_type}' assigned to '{email}' successfully!",
                "error": None,
                "license_types": db.LICENSE_TYPES,
                "prefill_email": "",
            },
        )
    else:
        # Check if user doesn't exist vs bad license
        user = db.get_user_by_email(email)
        if user is None:
            error_msg = f"❌ User '{email}' not found."
        else:
            error_msg = f"❌ Invalid license type '{license_type}'. Valid: {', '.join(db.LICENSE_TYPES)}"

        return templates.TemplateResponse(
            "assign_license.html",
            {
                "request": request,
                "message": None,
                "error": error_msg,
                "license_types": db.LICENSE_TYPES,
                "prefill_email": email,
            },
            status_code=400,
        )
