"""
In-memory database for the Mock IT Admin Panel.
Uses plain Python dicts to simulate a user store.
No external database required — perfect for demo/testing.
"""

import uuid
from datetime import datetime
from typing import Dict, Optional

# ---------------------------------------------------------------------------
# Data stores — module-level singletons (in-memory)
# ---------------------------------------------------------------------------

# Users dictionary: keyed by email
# Each user has: id, email, name, password, license, created_at, is_active
USERS: Dict[str, dict] = {
    "john@company.com": {
        "id": str(uuid.uuid4()),
        "email": "john@company.com",
        "name": "John Doe",
        "password": "password123",
        "license": "basic",
        "created_at": datetime.now().isoformat(),
        "is_active": True,
    },
    "jane@company.com": {
        "id": str(uuid.uuid4()),
        "email": "jane@company.com",
        "name": "Jane Smith",
        "password": "password123",
        "license": "pro",
        "created_at": datetime.now().isoformat(),
        "is_active": True,
    },
}

# Admin credentials (hardcoded for demo)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Available license types
LICENSE_TYPES = ["basic", "pro", "enterprise"]


# ---------------------------------------------------------------------------
# Helper functions — CRUD operations on the in-memory store
# ---------------------------------------------------------------------------

def get_all_users() -> list:
    """Return all users as a list of dicts."""
    return list(USERS.values())


def get_user_by_email(email: str) -> Optional[dict]:
    """Fetch a single user by their email address."""
    return USERS.get(email.lower())


def create_user(name: str, email: str, password: str, license_type: str = "basic") -> dict:
    """
    Create a new user and persist to in-memory store.
    Raises ValueError if user already exists.
    """
    email = email.lower()
    if email in USERS:
        raise ValueError(f"User with email '{email}' already exists.")

    user = {
        "id": str(uuid.uuid4()),
        "email": email,
        "name": name,
        "password": password,
        "license": license_type if license_type in LICENSE_TYPES else "basic",
        "created_at": datetime.now().isoformat(),
        "is_active": True,
    }
    USERS[email] = user
    return user


def reset_password(email: str, new_password: str) -> bool:
    """
    Reset a user's password.
    Returns True on success, False if user not found.
    """
    email = email.lower()
    if email not in USERS:
        return False
    USERS[email]["password"] = new_password
    return True


def assign_license(email: str, license_type: str) -> bool:
    """
    Assign a license to a user.
    Returns True on success, False if user or license not found.
    """
    email = email.lower()
    if email not in USERS or license_type not in LICENSE_TYPES:
        return False
    USERS[email]["license"] = license_type
    return True


def delete_user(email: str) -> bool:
    """Remove a user from the store."""
    email = email.lower()
    if email not in USERS:
        return False
    del USERS[email]
    return True


def get_stats() -> dict:
    """Return aggregate stats for the dashboard."""
    users = list(USERS.values())
    return {
        "total_users": len(users),
        "active_users": sum(1 for u in users if u["is_active"]),
        "pro_licenses": sum(1 for u in users if u["license"] == "pro"),
        "enterprise_licenses": sum(1 for u in users if u["license"] == "enterprise"),
        "basic_licenses": sum(1 for u in users if u["license"] == "basic"),
    }
