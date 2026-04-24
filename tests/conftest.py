"""
Shared pytest fixtures for the Intelligence Query Engine test suite.

Session-scoped fixtures create the Flask test app and database schema once
per test session.  Function-scoped fixtures provide a fresh test client for
each test.
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, settings

from app import create_app
from app.db.schema import create_all_tables, drop_all_tables
from app.extensions import get_engine

# ---------------------------------------------------------------------------
# Hypothesis profile
# ---------------------------------------------------------------------------
settings.register_profile(
    "ci",
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile("ci")


# ---------------------------------------------------------------------------
# Flask app fixture (session-scoped)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def app():
    """Create a Flask test application and set up the database schema."""
    flask_app = create_app("testing")

    with flask_app.app_context():
        engine = get_engine(flask_app)
        # Ensure a clean slate for the test session.
        drop_all_tables(engine)
        create_all_tables(engine)
        yield flask_app
        drop_all_tables(engine)


# ---------------------------------------------------------------------------
# Test client fixture (function-scoped)
# ---------------------------------------------------------------------------

@pytest.fixture
def client(app):
    """Return a Flask test client."""
    return app.test_client()
