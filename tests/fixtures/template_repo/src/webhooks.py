"""Webhook notification system for widget events."""

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class WebhookConfig:
    url: str
    events: list[str]
    secret: Optional[str] = None
    active: bool = True
    retry_count: int = 3
    timeout_seconds: int = 30


def compute_signature(payload: str, secret: str) -> str:
    """Compute HMAC-SHA256 signature for webhook payload."""
    return hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def build_payload(event_type: str, data: dict) -> str:
    """Build webhook payload JSON."""
    return json.dumps({
        "event": event_type,
        "timestamp": int(time.time()),
        "data": data,
    })


def should_deliver(config: WebhookConfig, event_type: str) -> bool:
    """Check if a webhook should fire for this event type."""
    if not config.active:
        return False
    if "*" in config.events:
        return True
    return event_type in config.events


class WebhookRegistry:
    def __init__(self):
        self._hooks: list[WebhookConfig] = []

    def register(self, config: WebhookConfig) -> None:
        self._hooks.append(config)

    def unregister(self, url: str) -> None:
        self._hooks = [h for h in self._hooks if h.url != url]

    def get_deliverable(self, event_type: str) -> list[WebhookConfig]:
        return [h for h in self._hooks if should_deliver(h, event_type)]
