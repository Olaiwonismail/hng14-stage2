from __future__ import annotations

from typing import Any


def serialise_profile(row: Any) -> dict:
    """Convert a SQLAlchemy RowMapping (or any dict-like row) to a JSON-serialisable dict.

    Args:
        row: A dict-like object with profile fields.

    Returns:
        A dict with all profile fields formatted for JSON serialisation.
        ``created_at`` is formatted as a UTC ISO 8601 string (``YYYY-MM-DDTHH:MM:SSZ``),
        or ``None`` if the value is absent.
        ``id`` is always cast to ``str``.
    """
    created_at = row["created_at"]
    created_at_str = created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if created_at is not None else None

    return {
        "id": str(row["id"]),
        "name": row["name"],
        "gender": row["gender"],
        "gender_probability": row["gender_probability"],
        "age": row["age"],
        "age_group": row["age_group"],
        "country_id": row["country_id"],
        "country_name": row["country_name"],
        "country_probability": row["country_probability"],
        "created_at": created_at_str,
    }
