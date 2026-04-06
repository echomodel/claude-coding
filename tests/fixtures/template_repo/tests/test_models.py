"""Tests for widget data models."""

from datetime import datetime

from src.models import Widget, WidgetBatch, WidgetStatus, Priority


def test_widget_defaults():
    w = Widget(id="w1", name="Test", description="A test widget")
    assert w.status == WidgetStatus.DRAFT
    assert w.priority == Priority.MEDIUM
    assert w.tags == []
    assert w.owner_id is None


def test_widget_activate():
    w = Widget(id="w1", name="Test", description="desc")
    w.activate()
    assert w.status == WidgetStatus.ACTIVE
    assert w.updated_at is not None


def test_widget_archive():
    w = Widget(id="w1", name="Test", description="desc")
    w.activate()
    w.archive()
    assert w.status == WidgetStatus.ARCHIVED


def test_widget_add_tag():
    w = Widget(id="w1", name="Test", description="desc")
    w.add_tag("important")
    w.add_tag("urgent")
    w.add_tag("important")  # duplicate
    assert w.tags == ["important", "urgent"]


def test_batch_counts():
    batch = WidgetBatch()
    batch.widgets.append(Widget(id="w1", name="A", description="a"))
    batch.widgets.append(Widget(id="w2", name="B", description="b"))
    batch.widgets[0].activate()
    assert batch.total == 2
    assert batch.active_count == 1
