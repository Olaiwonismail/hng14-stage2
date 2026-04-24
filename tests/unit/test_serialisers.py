"""Unit tests for app/serialisers.py — serialise_profile function.

Validates: Requirements 7.1, 7.2
"""
from __future__ import annotations

import datetime

import pytest

from app.serialisers import serialise_profile


def _make_row(overrides: dict | None = None) -> dict:
    """Return a minimal valid row dict, optionally overriding fields."""
    base = {
        "id": "018f4e3a-7b2c-7000-8000-000000000001",
        "name": "Amara Osei",
        "gender": "female",
        "gender_probability": 0.97,
        "age": 28,
        "age_group": "adult",
        "country_id": "GH",
        "country_name": "Ghana",
        "country_probability": 0.89,
        "created_at": datetime.datetime(2024, 1, 15, 10, 30, 0),
    }
    if overrides:
        base.update(overrides)
    return base


class TestSerialiseProfile:
    # ------------------------------------------------------------------
    # created_at formatting — Requirement 7.1
    # ------------------------------------------------------------------

    def test_created_at_formatted_as_utc_iso8601(self):
        row = _make_row({"created_at": datetime.datetime(2024, 1, 15, 10, 30, 0)})
        result = serialise_profile(row)
        assert result["created_at"] == "2024-01-15T10:30:00Z"

    def test_created_at_midnight(self):
        row = _make_row({"created_at": datetime.datetime(2000, 6, 1, 0, 0, 0)})
        result = serialise_profile(row)
        assert result["created_at"] == "2000-06-01T00:00:00Z"

    def test_created_at_none_returns_none(self):
        row = _make_row({"created_at": None})
        result = serialise_profile(row)
        assert result["created_at"] is None

    # ------------------------------------------------------------------
    # id cast to string — Requirement 7.2
    # ------------------------------------------------------------------

    def test_id_returned_as_string_when_already_string(self):
        row = _make_row({"id": "018f4e3a-7b2c-7000-8000-000000000001"})
        result = serialise_profile(row)
        assert isinstance(result["id"], str)
        assert result["id"] == "018f4e3a-7b2c-7000-8000-000000000001"

    def test_id_cast_to_string_when_integer(self):
        row = _make_row({"id": 42})
        result = serialise_profile(row)
        assert isinstance(result["id"], str)
        assert result["id"] == "42"

    # ------------------------------------------------------------------
    # All expected keys are present
    # ------------------------------------------------------------------

    def test_all_expected_keys_present(self):
        row = _make_row()
        result = serialise_profile(row)
        expected_keys = {
            "id", "name", "gender", "gender_probability",
            "age", "age_group", "country_id", "country_name",
            "country_probability", "created_at",
        }
        assert set(result.keys()) == expected_keys

    # ------------------------------------------------------------------
    # Passthrough fields are not mutated
    # ------------------------------------------------------------------

    def test_passthrough_fields_unchanged(self):
        row = _make_row()
        result = serialise_profile(row)
        assert result["name"] == "Amara Osei"
        assert result["gender"] == "female"
        assert result["gender_probability"] == 0.97
        assert result["age"] == 28
        assert result["age_group"] == "adult"
        assert result["country_id"] == "GH"
        assert result["country_name"] == "Ghana"
        assert result["country_probability"] == 0.89

    # ------------------------------------------------------------------
    # Pure function — original row is not mutated
    # ------------------------------------------------------------------

    def test_original_row_not_mutated(self):
        row = _make_row()
        original_created_at = row["created_at"]
        serialise_profile(row)
        assert row["created_at"] == original_created_at
