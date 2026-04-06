"""Tests for widget service operations."""

import pytest

from src.models import WidgetStatus, Priority
from src.service import WidgetService, WidgetNotFoundError


@pytest.fixture
def service():
    return WidgetService()


def test_create_widget(service):
    w = service.create("Dashboard", "Main dashboard widget")
    assert w.name == "Dashboard"
    assert w.status == WidgetStatus.DRAFT


def test_get_widget(service):
    created = service.create("Test", "Test widget")
    fetched = service.get(created.id)
    assert fetched.id == created.id


def test_get_nonexistent_raises(service):
    with pytest.raises(WidgetNotFoundError):
        service.get("nonexistent-id")


def test_list_all(service):
    service.create("A", "First")
    service.create("B", "Second")
    service.create("C", "Third")
    assert len(service.list_all()) == 3


def test_list_by_status(service):
    w1 = service.create("Active One", "desc")
    w2 = service.create("Draft One", "desc")
    w1.activate()
    service._storage[w1.id] = w1
    active = service.list_all(status=WidgetStatus.ACTIVE)
    assert len(active) == 1
    assert active[0].id == w1.id


def test_update_widget(service):
    w = service.create("Original", "desc")
    updated = service.update(w.id, name="Renamed")
    assert updated.name == "Renamed"


def test_delete_widget(service):
    w = service.create("ToDelete", "desc")
    service.delete(w.id)
    with pytest.raises(WidgetNotFoundError):
        service.get(w.id)


def test_batch_create(service):
    items = [
        {"name": "Batch A", "description": "First in batch"},
        {"name": "Batch B", "description": "Second in batch"},
    ]
    batch = service.batch_create(items)
    assert batch.total == 2
    assert len(service.list_all()) == 2


def test_search(service):
    service.create("Weather Widget", "Shows forecast")
    service.create("Clock Widget", "Shows time")
    service.create("News Feed", "Latest headlines")
    results = service.search("widget")
    assert len(results) == 2
