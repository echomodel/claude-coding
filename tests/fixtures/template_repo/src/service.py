"""Core service layer for widget operations."""

import uuid
from datetime import datetime
from typing import Optional

from .models import Widget, WidgetBatch, WidgetStatus, Priority


class WidgetNotFoundError(Exception):
    pass


class WidgetService:
    def __init__(self, storage=None):
        self._storage = storage or {}

    def create(self, name: str, description: str,
               priority: Priority = Priority.MEDIUM,
               tags: Optional[list[str]] = None) -> Widget:
        widget = Widget(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            priority=priority,
            tags=tags or [],
        )
        self._storage[widget.id] = widget
        return widget

    def get(self, widget_id: str) -> Widget:
        if widget_id not in self._storage:
            raise WidgetNotFoundError(f"Widget {widget_id} not found")
        return self._storage[widget_id]

    def list_all(self, status: Optional[WidgetStatus] = None) -> list[Widget]:
        widgets = list(self._storage.values())
        if status:
            widgets = [w for w in widgets if w.status == status]
        return sorted(widgets, key=lambda w: w.created_at, reverse=True)

    def update(self, widget_id: str, **kwargs) -> Widget:
        widget = self.get(widget_id)
        for key, value in kwargs.items():
            if hasattr(widget, key):
                setattr(widget, key, value)
        widget.updated_at = datetime.utcnow()
        self._storage[widget_id] = widget
        return widget

    def delete(self, widget_id: str) -> None:
        if widget_id not in self._storage:
            raise WidgetNotFoundError(f"Widget {widget_id} not found")
        del self._storage[widget_id]

    def batch_create(self, items: list[dict]) -> WidgetBatch:
        batch = WidgetBatch(batch_id=str(uuid.uuid4()))
        for item in items:
            widget = self.create(**item)
            batch.widgets.append(widget)
        return batch

    def search(self, query: str) -> list[Widget]:
        query_lower = query.lower()
        return [
            w for w in self._storage.values()
            if query_lower in w.name.lower()
            or query_lower in w.description.lower()
            or any(query_lower in t.lower() for t in w.tags)
        ]
