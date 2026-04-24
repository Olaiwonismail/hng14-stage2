"""
Integration tests for GET /api/profiles/search.

Tests verify that the NL parser correctly maps plain-English queries to
filters, that pagination works, and that error cases return the right shapes.
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Seed helper (reuse from profiles test module)
# ---------------------------------------------------------------------------

def _seed_profiles(app, profiles: list[dict]) -> None:
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
def seed_search_data(app):
    """Seed deterministic data for search endpoint tests."""
    profiles = [
        {
            "name": "Search Alice",
            "gender": "female",
            "gender_probability": 0.95,
            "age": 20,
            "age_group": "adult",
            "country_id": "NG",
            "country_name": "Nigeria",
            "country_probability": 0.90,
        },
        {
            "name": "Search Bob",
            "gender": "male",
            "gender_probability": 0.88,
            "age": 17,
            "age_group": "teenager",
            "country_id": "KE",
            "country_name": "Kenya",
            "country_probability": 0.75,
        },
        {
            "name": "Search Carol",
            "gender": "female",
            "gender_probability": 0.92,
            "age": 65,
            "age_group": "senior",
            "country_id": "GH",
            "country_name": "Ghana",
            "country_probability": 0.80,
        },
        {
            "name": "Search Dave",
            "gender": "male",
            "gender_probability": 0.70,
            "age": 8,
            "age_group": "child",
            "country_id": "NG",
            "country_name": "Nigeria",
            "country_probability": 0.60,
        },
        {
            "name": "Search Eve",
            "gender": "female",
            "gender_probability": 0.99,
            "age": 22,
            "age_group": "adult",
            "country_id": "ZA",
            "country_name": "South Africa",
            "country_probability": 0.85,
        },
    ]
    _seed_profiles(app, profiles)
    yield


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

class TestSearchErrors:
    def test_missing_q_returns_400(self, client):
        resp = client.get("/api/profiles/search")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["status"] == "error"
        assert data["message"] == "Missing or empty parameter"

    def test_empty_q_returns_400(self, client):
        resp = client.get("/api/profiles/search?q=")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["status"] == "error"
        assert data["message"] == "Missing or empty parameter"

    def test_unrecognised_q_returns_error(self, client):
        resp = client.get("/api/profiles/search?q=xyzzy+foobar+baz")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["status"] == "error"
        assert data["message"] == "Unable to interpret query"

    def test_limit_over_50_returns_400(self, client):
        resp = client.get("/api/profiles/search?q=males&limit=51")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Gender parsing
# ---------------------------------------------------------------------------

class TestGenderParsing:
    def test_males_query_returns_only_males(self, client):
        resp = client.get("/api/profiles/search?q=males&limit=50")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        for p in data["data"]:
            assert p["gender"] == "male"

    def test_females_query_returns_only_females(self, client):
        resp = client.get("/api/profiles/search?q=females&limit=50")
        data = resp.get_json()
        for p in data["data"]:
            assert p["gender"] == "female"

    def test_male_and_female_returns_all_genders(self, client):
        resp_all = client.get("/api/profiles/search?q=male+and+female&limit=50")
        resp_male = client.get("/api/profiles/search?q=males&limit=50")
        resp_female = client.get("/api/profiles/search?q=females&limit=50")
        total_all = resp_all.get_json()["total"]
        total_male = resp_male.get_json()["total"]
        total_female = resp_female.get_json()["total"]
        # "male and female" should return at least as many as either alone
        assert total_all >= total_male
        assert total_all >= total_female


# ---------------------------------------------------------------------------
# Age parsing
# ---------------------------------------------------------------------------

class TestAgeParsing:
    def test_young_maps_to_16_24(self, client):
        resp = client.get("/api/profiles/search?q=young+people&limit=50")
        data = resp.get_json()
        for p in data["data"]:
            assert 16 <= p["age"] <= 24

    def test_above_age(self, client):
        resp = client.get("/api/profiles/search?q=people+above+30&limit=50")
        data = resp.get_json()
        for p in data["data"]:
            assert p["age"] >= 30

    def test_below_age(self, client):
        resp = client.get("/api/profiles/search?q=people+below+20&limit=50")
        data = resp.get_json()
        for p in data["data"]:
            assert p["age"] <= 20


# ---------------------------------------------------------------------------
# Age group parsing
# ---------------------------------------------------------------------------

class TestAgeGroupParsing:
    def test_teenagers_query(self, client):
        resp = client.get("/api/profiles/search?q=teenagers&limit=50")
        data = resp.get_json()
        for p in data["data"]:
            assert p["age_group"] == "teenager"

    def test_adults_query(self, client):
        resp = client.get("/api/profiles/search?q=adults&limit=50")
        data = resp.get_json()
        for p in data["data"]:
            assert p["age_group"] == "adult"

    def test_seniors_query(self, client):
        resp = client.get("/api/profiles/search?q=seniors&limit=50")
        data = resp.get_json()
        for p in data["data"]:
            assert p["age_group"] == "senior"

    def test_elderly_maps_to_senior(self, client):
        resp = client.get("/api/profiles/search?q=elderly+people&limit=50")
        data = resp.get_json()
        for p in data["data"]:
            assert p["age_group"] == "senior"


# ---------------------------------------------------------------------------
# Country parsing
# ---------------------------------------------------------------------------

class TestCountryParsing:
    def test_from_nigeria(self, client):
        resp = client.get("/api/profiles/search?q=people+from+nigeria&limit=50")
        data = resp.get_json()
        assert data["status"] == "success"
        for p in data["data"]:
            assert p["country_id"].upper() == "NG"

    def test_from_kenya(self, client):
        resp = client.get("/api/profiles/search?q=people+from+kenya&limit=50")
        data = resp.get_json()
        for p in data["data"]:
            assert p["country_id"].upper() == "KE"


# ---------------------------------------------------------------------------
# Multi-keyword (AND logic)
# ---------------------------------------------------------------------------

class TestMultiKeyword:
    def test_adult_males_from_nigeria(self, client):
        resp = client.get(
            "/api/profiles/search?q=adult+males+from+nigeria&limit=50"
        )
        data = resp.get_json()
        assert data["status"] == "success"
        for p in data["data"]:
            assert p["gender"] == "male"
            assert p["age_group"] == "adult"
            assert p["country_id"].upper() == "NG"

    def test_females_above_30(self, client):
        resp = client.get("/api/profiles/search?q=females+above+30&limit=50")
        data = resp.get_json()
        for p in data["data"]:
            assert p["gender"] == "female"
            assert p["age"] >= 30

    def test_search_equals_direct_filter(self, client):
        """Search endpoint and direct filter endpoint must return the same total."""
        search_resp = client.get(
            "/api/profiles/search?q=females+from+nigeria&limit=50"
        )
        direct_resp = client.get(
            "/api/profiles?gender=female&country_id=NG&limit=50"
        )
        assert search_resp.get_json()["total"] == direct_resp.get_json()["total"]


# ---------------------------------------------------------------------------
# Response structure
# ---------------------------------------------------------------------------

class TestSearchResponseStructure:
    def test_success_response_has_required_keys(self, client):
        resp = client.get("/api/profiles/search?q=males")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        assert "page" in data
        assert "limit" in data
        assert "total" in data
        assert isinstance(data["data"], list)

    def test_cors_header_present(self, client):
        resp = client.get("/api/profiles/search?q=males")
        assert resp.headers.get("Access-Control-Allow-Origin") == "*"

    def test_pagination_params_respected(self, client):
        resp = client.get("/api/profiles/search?q=males&page=1&limit=2")
        data = resp.get_json()
        assert data["page"] == 1
        assert data["limit"] == 2
        assert len(data["data"]) <= 2
