"""
Idempotent database seeder for the Intelligence Query Engine.

Usage
-----
    python scripts/seed.py

Reads ``data/profiles.json`` relative to the project root, generates a
UUID v7 for each record, and inserts them into the ``profiles`` table using
``INSERT ... ON CONFLICT (name) DO NOTHING`` so that re-running the script
never creates duplicate records.

Environment
-----------
Requires ``DATABASE_URL`` to be set (via ``.env`` or the environment).
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so we can import app modules.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
from sqlalchemy import create_engine, insert, text
from sqlalchemy.exc import SQLAlchemyError

load_dotenv(PROJECT_ROOT / ".env")

from app.db.schema import create_all_tables, profiles_table  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DATA_FILE = PROJECT_ROOT / "data" / "profiles.json"
BATCH_SIZE = 200  # rows per INSERT statement

_AGE_GROUP_MAP = [
    (0, 12, "child"),
    (13, 19, "teenager"),
    (20, 59, "adult"),
    (60, 999, "senior"),
]


def _derive_age_group(age: int) -> str:
    """Return the age_group string for a given age."""
    for lo, hi, group in _AGE_GROUP_MAP:
        if lo <= age <= hi:
            return group
    return "adult"


def _generate_uuid7() -> str:
    """Generate a UUID v7 string using the uuid_utils package."""
    try:
        import uuid_utils
        return str(uuid_utils.uuid7())
    except ImportError:
        # Fallback: use uuid4 if uuid_utils is not installed (should not
        # happen in production, but avoids a hard crash during development).
        import uuid
        log.warning("uuid_utils not found; falling back to uuid4.")
        return str(uuid.uuid4())


def load_profiles(path: Path) -> list[dict]:
    """Load and return the list of profile dicts from *path*."""
    if not path.exists():
        log.error("Seed file not found: %s", path)
        sys.exit(1)

    try:
        with path.open(encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        log.error("Failed to read seed file %s: %s", path, exc)
        sys.exit(1)

    profiles = raw.get("profiles") if isinstance(raw, dict) else raw
    if not isinstance(profiles, list):
        log.error("Expected a list of profiles in %s", path)
        sys.exit(1)

    return profiles


def seed(database_url: str | None = None) -> None:
    """Run the seeder against the database specified by *database_url*.

    If *database_url* is ``None``, reads ``DATABASE_URL`` from the
    environment.
    """
    url = database_url or os.environ.get("DATABASE_URL")
    if not url:
        log.error(
            "DATABASE_URL is not set. "
            "Add it to your .env file or pass it as an argument."
        )
        sys.exit(1)

    profiles = load_profiles(DATA_FILE)
    log.info("Loaded %d profiles from %s", len(profiles), DATA_FILE)

    engine = create_engine(url, pool_pre_ping=True)

    # Ensure the schema exists before inserting.
    try:
        create_all_tables(engine)
    except SQLAlchemyError as exc:
        log.error("Failed to create tables: %s", exc)
        sys.exit(1)

    # Build rows, generating a UUID v7 for each.
    rows = []
    for p in profiles:
        age = int(p.get("age", 0))
        row = {
            "id": _generate_uuid7(),
            "name": p["name"],
            "gender": p["gender"],
            "gender_probability": float(p.get("gender_probability", 0.0)),
            "age": age,
            "age_group": p.get("age_group") or _derive_age_group(age),
            "country_id": p["country_id"],
            "country_name": p["country_name"],
            "country_probability": float(p.get("country_probability", 0.0)),
        }
        rows.append(row)

    inserted = 0
    skipped = 0

    try:
        with engine.begin() as conn:
            for batch_start in range(0, len(rows), BATCH_SIZE):
                batch = rows[batch_start : batch_start + BATCH_SIZE]
                stmt = insert(profiles_table).values(batch)
                # ON CONFLICT (name) DO NOTHING — idempotent re-runs
                stmt = stmt.on_conflict_do_nothing(index_elements=["name"])
                result = conn.execute(stmt)
                inserted += result.rowcount
                skipped += len(batch) - result.rowcount

    except SQLAlchemyError as exc:
        log.error("Database error during seeding: %s", exc)
        sys.exit(1)

    log.info(
        "Seeding complete — inserted: %d, skipped (already existed): %d",
        inserted,
        skipped,
    )


if __name__ == "__main__":
    seed()
