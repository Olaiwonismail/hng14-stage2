"""
Flask extension helpers for the Intelligence Query Engine.

Provides:
  - init_db(app)   — creates a SQLAlchemy Engine and attaches it to the app
  - get_engine(app) — retrieves the Engine stored on the app
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import create_engine, Engine

if TYPE_CHECKING:
    from flask import Flask

_DB_ENGINE_KEY = "db_engine"


def init_db(app: "Flask") -> None:
    """Create a SQLAlchemy Engine from ``app.config["DATABASE_URL"]`` and
    store it on ``app.extensions["db_engine"]``.

    ``pool_pre_ping=True`` causes SQLAlchemy to issue a lightweight
    ``SELECT 1`` before handing out a connection, which transparently
    recovers from stale connections (e.g. after a database restart).
    """
    database_url: str | None = app.config.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. "
            "Add it to your .env file or set it as an environment variable."
        )

    engine: Engine = create_engine(
        database_url,
        pool_pre_ping=True,
    )

    # app.extensions is a plain dict; store the engine under a namespaced key.
    app.extensions[_DB_ENGINE_KEY] = engine


def get_engine(app: "Flask") -> Engine:
    """Return the SQLAlchemy Engine attached to *app*.

    Raises ``RuntimeError`` if ``init_db`` has not been called yet.
    """
    try:
        return app.extensions[_DB_ENGINE_KEY]
    except KeyError:
        raise RuntimeError(
            "Database engine not initialised. "
            "Call init_db(app) inside your application factory."
        )
