"""Data models for the widget service."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class WidgetStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Widget:
    id: str
    name: str
    description: str
    status: WidgetStatus = WidgetStatus.DRAFT
    priority: Priority = Priority.MEDIUM
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    owner_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def activate(self) -> None:
        self.status = WidgetStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def archive(self) -> None:
        self.status = WidgetStatus.ARCHIVED
        self.updated_at = datetime.utcnow()

    def add_tag(self, tag: str) -> None:
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()


@dataclass
class WidgetBatch:
    widgets: list[Widget] = field(default_factory=list)
    batch_id: Optional[str] = None

    @property
    def active_count(self) -> int:
        return sum(1 for w in self.widgets if w.status == WidgetStatus.ACTIVE)

    @property
    def total(self) -> int:
        return len(self.widgets)
