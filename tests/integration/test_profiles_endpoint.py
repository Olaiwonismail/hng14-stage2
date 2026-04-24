"""
Integration tests for GET /api/profiles.

These tests run against a real (test) PostgreSQL database.  The conftest
fixtures create the schema and seed a small dataset before the session starts.
"""

from __future__ import annotations

import re
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_profiles(app, profiles: list[dict]) -> None:
    """Insert test profiles directly into the DB."""
    import uuid_utils
    from sqlalchemy import insert
    from app.db.schema import profiles_table
    from app.extensions import get_engine

    with app.app_context():
        engine = get_engine(app)
        rows = [{"id": str(uuid_utils.uuid7()), **p} for p in profiles]
        with engine.begin() as conn:
            stmt = insert(profiles_table).values(rows).on_conflict_do_nothing(
                index_elements=["name"]
            )
            conn.execute(stmt)


@pytest.fixture(scope="module", autouse=True)
def seed_test_data(app):
    """Seed a small, deterministic dataset for the profiles endpoint tests."""
    profiles = [
        {
            "name": "Test Alice",
            "gender": "female",
            "gender_probability": 0.95,
            "age": 28,
            "age_group": "adult",
            "country_id": "NG",
            "country_name": "Nigeria",
            "country_probability": 0.90,
        },
        {
            "name": "Test Bob",
            "gender": "male",
            "gender_probability": 0.88,
            "age": 17,
            "age_group": "teenager",
            "country_id": "KE",
            "country_name": "Kenya",
            "country_probability": 0.75,
        },
        {
            "name": "Test Carol",
            "gender": "female",
            "gender_probability": 0.92,
            "age": 65,
            "age_group": "senior",
            "country_id": "GH",
            "country_name": "Ghana",
            "country_probability": 0.80,
        },
        {
            "name": "Test Dave",
            "gender": "male",
            "gender_probability": 0.70,
            "age": 8,
            "age_group": "child",
            "country_id": "NG",
            "country_name": "Nigeria",
            "country_probability": 0.60,
        },
        {
            "name": "Test Eve",
            "gender": "female",
            "gender_probability": 0.99,
            "age": 35,
            "age_group": "adult",
            "country_id": "ZA",
            "country_name": "South Africa",
            "country_probability": 0.85,
        },
    ]
    _seed_profiles(app, profiles)
    yield


# ---------------------------------------------------------------------------
# Response structure
# ---------------------------------------------------------------------------

class TestResponseStructure:
    def test_success_response_has_required_keys(self, client):
        resp = client.get("/api/profiles")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        assert "page" in data
        assert "limit" in data
        assert "total" in data
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_default_limit_is_10(self, client):
        resp = client.get("/api/profiles")
        data = resp.get_json()
        assert data["limit"] == 10

    def test_default_page_is_1(self, client):
        resp = client.get("/api/profiles")
        data = resp.get_json()
        assert data["page"] == 1

    def test_total_is_non_negative(self, client):
        resp = client.get("/api/profiles")
        data = resp.get_json()
        assert data["total"] >= 0

    def test_data_length_lte_limit(self, client):
        resp = client.get("/api/profiles?limit=3")
        data = resp.get_json()
        assert len(data["data"]) <= 3


# ---------------------------------------------------------------------------
# Profile object shape
# ---------------------------------------------------------------------------

class TestProfileShape:
    REQUIRED_FIELDS = {
        "id", "name", "gender", "gender_probability",
        "age", "age_group", "country_id", "country_name",
        "country_probability", "created_at",
    }
    _TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    def test_profile_has_all_fields(self, client):
        resp = client.get("/api/profiles?limit=1")
        data = resp.get_json()
        if data["data"]:
            profile = data["data"][0]
            assert self.REQUIRED_FIELDS.issubset(profile.keys())

    def test_created_at_is_utc_iso8601(self, client):
        resp = client.get("/api/profiles?limit=5")
        data = resp.get_json()
        for profile in data["data"]:
            assert self._TS_RE.match(profile["created_at"]), (
                f"created_at {profile['created_at']!r} is not UTC ISO 8601"
            )

    def test_id_is_string(self, client):
        resp = client.get("/api/profiles?limit=1")
        data = resp.get_json()
        if data["data"]:
            assert isinstance(data["data"][0]["id"], str)


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

class TestFiltering:
    def test_filter_by_gender_male(self, client):
        resp = client.get("/api/profiles?gender=male&limit=50")
        data = resp.get_json()
        assert data["status"] == "success"
        for p in data["data"]:
            assert p["gender"] == "male"

    def test_filter_by_gender_female(self, client):
        resp = client.get("/api/profiles?gender=female&limit=50")
        data = resp.get_json()
        for p in data["data"]:
            assert p["gender"] == "female"

    def test_filter_by_age_group(self, client):
        resp = client.get("/api/profiles?age_group=adult&limit=50")
        data = resp.get_json()
        for p in data["data"]:
            assert p["age_group"] == "adult"

    def test_filter_by_country_id(self, client):
        resp = client.get("/api/profiles?country_id=NG&limit=50")
        data = resp.get_json()
        for p in data["data"]:
            assert p["country_id"].upper() == "NG"

    def test_filter_by_country_id_case_insensitive(self, client):
        resp_upper = client.get("/api/profiles?country_id=NG&limit=50")
        resp_lower = client.get("/api/profiles?country_id=ng&limit=50")
        assert resp_upper.get_json()["total"] == resp_lower.get_json()["total"]

    def test_filter_min_age(self, client):
        resp = client.get("/api/profiles?min_age=30&limit=50")
        data = resp.get_json()
        for p in data["data"]:
            assert p["age"] >= 30

    def test_filter_max_age(self, client):
        resp = client.get("/api/profiles?max_age=20&limit=50")
        data = resp.get_json()
        for p in data["data"]:
            assert p["age"] <= 20

    def test_combined_filters(self, client):
        resp = client.get("/api/profiles?gender=female&age_group=adult&limit=50")
        data = resp.get_json()
        for p in data["data"]:
            assert p["gender"] == "female"
            assert p["age_group"] == "adult"

    def test_filter_min_gender_probability(self, client):
        resp = client.get("/api/profiles?min_gender_probability=0.9&limit=50")
        data = resp.get_json()
        for p in data["data"]:
            assert p["gender_probability"] >= 0.9

    def test_filter_min_country_probability(self, client):
        resp = client.get("/api/profiles?min_country_probability=0.8&limit=50")
        data = resp.get_json()
        for p in data["data"]:
            assert p["country_probability"] >= 0.8


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------

class TestSorting:
    def test_sort_by_age_asc(self, client):
        resp = client.get("/api/profiles?sort_by=age&order=asc&limit=50")
        data = resp.get_json()
        ages = [p["age"] for p in data["data"]]
        assert ages == sorted(ages)

    def test_sort_by_age_desc(self, client):
        resp = client.get("/api/profiles?sort_by=age&order=desc&limit=50")
        data = resp.get_json()
        ages = [p["age"] for p in data["data"]]
        assert ages == sorted(ages, reverse=True)

    def test_sort_by_gender_probability_asc(self, client):
        resp = client.get("/api/profiles?sort_by=gender_probability&order=asc&limit=50")
        data = resp.get_json()
        probs = [p["gender_probability"] for p in data["data"]]
        assert probs == sorted(probs)


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

class TestPagination:
    def test_limit_respected(self, client):
        resp = client.get("/api/profiles?limit=2")
        data = resp.get_json()
        assert len(data["data"]) <= 2

    def test_page_2_differs_from_page_1(self, client):
        resp1 = client.get("/api/profiles?limit=2&page=1")
        resp2 = client.get("/api/profiles?limit=2&page=2")
        ids1 = {p["id"] for p in resp1.get_json()["data"]}
        ids2 = {p["id"] for p in resp2.get_json()["data"]}
        # Pages should not overlap (assuming enough records exist)
        if ids1 and ids2:
            assert ids1.isdisjoint(ids2)

    def test_total_consistent_across_pages(self, client):
        resp1 = client.get("/api/profiles?limit=2&page=1")
        resp2 = client.get("/api/profiles?limit=2&page=2")
        assert resp1.get_json()["total"] == resp2.get_json()["total"]

    def test_limit_max_50(self, client):
        resp = client.get("/api/profiles?limit=51")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["status"] == "error"


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

class TestValidationErrors:
    def test_unknown_param_returns_400(self, client):
        resp = client.get("/api/profiles?foo=bar")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["status"] == "error"

    def test_invalid_gender_returns_400(self, client):
        resp = client.get("/api/profiles?gender=other")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["status"] == "error"

    def test_invalid_age_group_returns_400(self, client):
        resp = client.get("/api/profiles?age_group=young")
        assert resp.status_code == 400

    def test_invalid_sort_by_returns_400(self, client):
        resp = client.get("/api/profiles?sort_by=name")
        assert resp.status_code == 400

    def test_invalid_order_returns_400(self, client):
        resp = client.get("/api/profiles?order=random")
        assert resp.status_code == 400

    def test_non_integer_min_age_returns_422(self, client):
        resp = client.get("/api/profiles?min_age=abc")
        assert resp.status_code == 422
        data = resp.get_json()
        assert data["status"] == "error"
        assert data["message"] == "Invalid parameter type"

    def test_non_float_min_gender_probability_returns_422(self, client):
        resp = client.get("/api/profiles?min_gender_probability=high")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

class TestCORS:
    def test_cors_header_present(self, client):
        resp = client.get("/api/profiles")
        assert resp.headers.get("Access-Control-Allow-Origin") == "*"

    def test_options_preflight_returns_200(self, client):
        resp = client.options(
            "/api/profiles",
            headers={"Origin": "https://example.com"},
        )
        assert resp.status_code == 200
