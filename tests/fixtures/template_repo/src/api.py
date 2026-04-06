"""HTTP API handlers for the widget service."""

import json
from typing import Any


def parse_request(raw: str) -> dict[str, Any]:
    """Parse incoming JSON request body."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON"}


def format_response(data: Any, status: int = 200) -> dict:
    """Format a standard API response."""
    return {
        "status": status,
        "data": data,
    }


def format_error(message: str, status: int = 400) -> dict:
    return {
        "status": status,
        "error": message,
    }


def validate_widget_payload(payload: dict) -> list[str]:
    """Validate widget creation payload. Returns list of errors."""
    errors = []
    if not payload.get("name"):
        errors.append("name is required")
    if len(payload.get("name", "")) > 200:
        errors.append("name must be under 200 characters")
    if not payload.get("description"):
        errors.append("description is required")
    if payload.get("priority") and payload["priority"] not in range(1, 5):
        errors.append("priority must be 1-4")
    return errors


def paginate(items: list, page: int = 1, per_page: int = 20) -> dict:
    """Paginate a list of items."""
    start = (page - 1) * per_page
    end = start + per_page
    return {
        "items": items[start:end],
        "page": page,
        "per_page": per_page,
        "total": len(items),
        "pages": (len(items) + per_page - 1) // per_page,
    }
