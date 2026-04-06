"""Tests for API handlers."""

from src.api import (
    parse_request,
    format_response,
    format_error,
    validate_widget_payload,
    paginate,
)


def test_parse_valid_json():
    result = parse_request('{"name": "test"}')
    assert result == {"name": "test"}


def test_parse_invalid_json():
    result = parse_request("not json")
    assert "error" in result


def test_format_response():
    resp = format_response({"id": "123"})
    assert resp["status"] == 200
    assert resp["data"]["id"] == "123"


def test_format_error():
    resp = format_error("not found", 404)
    assert resp["status"] == 404
    assert resp["error"] == "not found"


def test_validate_missing_name():
    errors = validate_widget_payload({"description": "test"})
    assert "name is required" in errors


def test_validate_missing_description():
    errors = validate_widget_payload({"name": "test"})
    assert "description is required" in errors


def test_validate_valid_payload():
    errors = validate_widget_payload({"name": "test", "description": "desc"})
    assert errors == []


def test_paginate_first_page():
    items = list(range(50))
    result = paginate(items, page=1, per_page=10)
    assert len(result["items"]) == 10
    assert result["total"] == 50
    assert result["pages"] == 5


def test_paginate_last_page():
    items = list(range(25))
    result = paginate(items, page=3, per_page=10)
    assert len(result["items"]) == 5
