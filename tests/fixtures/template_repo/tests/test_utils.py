"""Tests for shared utilities."""

from src.utils import slugify, truncate, parse_tags, is_valid_uuid


def test_slugify():
    assert slugify("Hello World") == "hello-world"
    assert slugify("  spaces  ") == "spaces"
    assert slugify("Special!@#Chars") == "specialchars"


def test_truncate_short():
    assert truncate("short", 100) == "short"


def test_truncate_long():
    result = truncate("a" * 200, 50)
    assert len(result) == 50
    assert result.endswith("...")


def test_parse_tags():
    assert parse_tags("a, b, c") == ["a", "b", "c"]
    assert parse_tags("  one  ,  two  ") == ["one", "two"]
    assert parse_tags("") == []


def test_valid_uuid():
    assert is_valid_uuid("a1b2c3d4" + "-e5f6-" + "7890-abcd-" + "ef1234567890")
    assert not is_valid_uuid("not-a-uuid")
    assert not is_valid_uuid("")
