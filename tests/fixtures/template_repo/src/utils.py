"""Shared utilities for the widget service."""

import re
from datetime import datetime, timezone


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def truncate(text: str, max_length: int = 100) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def parse_tags(raw: str) -> list[str]:
    """Parse comma-separated tags, stripping whitespace."""
    return [t.strip() for t in raw.split(",") if t.strip()]


def format_timestamp(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def is_valid_uuid(value: str) -> bool:
    pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )
    return bool(pattern.match(value))
