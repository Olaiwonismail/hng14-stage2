"""
Rule-based natural language query parser for the Intelligence Query Engine.

``parse_query`` is a **pure function** — it has no side effects and does not
call any external services or AI/LLM APIs.  It converts a plain-English
query string into a dict of filter parameters that can be passed directly
to ``build_profile_query``.

Supported patterns
------------------
Keyword / phrase          Mapped filter(s)
------------------------  ----------------------------------------
young                     min_age=16, max_age=24
male / males              gender=male
female / females          gender=female
male AND female together  gender filter omitted (all genders)
above N                   min_age=N
below N                   max_age=N
over N                    min_age=N  (alias for "above")
under N                   max_age=N  (alias for "below")
older than N              min_age=N
younger than N            max_age=N
child / children          age_group=child
teenager / teenagers      age_group=teenager
teen / teens              age_group=teenager
adult / adults            age_group=adult
senior / seniors          age_group=senior
elderly                   age_group=senior
from <country name>       country_id=<ISO alpha-2>
in <country name>         country_id=<ISO alpha-2>  (alias for "from")

Multiple keywords are combined with AND logic (dict merge).
"""

from __future__ import annotations

import re

from app.nl_parser.country_map import COUNTRY_MAP


class UninterpretableQueryError(ValueError):
    """Raised when a non-empty query string yields no recognisable filters."""


# ---------------------------------------------------------------------------
# Compiled regex patterns (case-insensitive)
# ---------------------------------------------------------------------------

_RE_FLAGS = re.IGNORECASE

# "young" — maps to ages 16–24 (parsing only; not a stored age_group)
_RE_YOUNG = re.compile(r"\byoung\b", _RE_FLAGS)

# Gender keywords
_RE_MALE = re.compile(r"\bmales?\b", _RE_FLAGS)
_RE_FEMALE = re.compile(r"\bfemales?\b", _RE_FLAGS)

# Age comparisons: "above N", "over N", "older than N"
_RE_MIN_AGE = re.compile(
    r"\b(?:above|over|older\s+than)\s+(\d+)\b", _RE_FLAGS
)

# Age comparisons: "below N", "under N", "younger than N"
_RE_MAX_AGE = re.compile(
    r"\b(?:below|under|younger\s+than)\s+(\d+)\b", _RE_FLAGS
)

# Age groups
_RE_CHILD = re.compile(r"\bchild(?:ren)?\b", _RE_FLAGS)
_RE_TEENAGER = re.compile(r"\bteens?(?:agers?)?\b", _RE_FLAGS)
_RE_ADULT = re.compile(r"\badults?\b", _RE_FLAGS)
_RE_SENIOR = re.compile(r"\b(?:seniors?|elderly)\b", _RE_FLAGS)

# Country: "from <name>" or "in <name>"
# Captures everything after "from"/"in" up to end-of-string or a comma/period.
_RE_COUNTRY = re.compile(
    r"\b(?:from|in)\s+([a-z][a-z\s'\u00c0-\u024f-]*?)(?:\s*(?:,|\.|\band\b|\bwho\b|\bwith\b|$))",
    _RE_FLAGS,
)


def _resolve_country(raw: str) -> str | None:
    """Look up a raw country string in COUNTRY_MAP.

    Tries the full string first, then progressively strips trailing words
    to handle phrases like "from nigeria above 30" where the regex may
    capture extra words.
    """
    candidate = raw.strip().lower()
    # Direct lookup
    if candidate in COUNTRY_MAP:
        return COUNTRY_MAP[candidate]
    # Strip trailing words one at a time
    words = candidate.split()
    for i in range(len(words) - 1, 0, -1):
        partial = " ".join(words[:i])
        if partial in COUNTRY_MAP:
            return COUNTRY_MAP[partial]
    return None


def parse_query(q: str) -> dict:
    """Parse a plain-English query string into a filter parameter dict.

    Parameters
    ----------
    q:
        The raw query string from the ``?q=`` parameter.

    Returns
    -------
    dict
        A dict whose keys are a subset of:
        ``gender``, ``age_group``, ``min_age``, ``max_age``, ``country_id``.
        All matched filters are combined with AND logic.

    Raises
    ------
    UninterpretableQueryError
        If *q* is non-empty but no patterns match.
    """
    if not q or not q.strip():
        raise UninterpretableQueryError("Query string is empty.")

    filters: dict = {}

    # --- Gender ---
    has_male = bool(_RE_MALE.search(q))
    has_female = bool(_RE_FEMALE.search(q))

    if has_male and has_female:
        # Both genders mentioned → omit gender filter (return all genders)
        pass
    elif has_male:
        filters["gender"] = "male"
    elif has_female:
        filters["gender"] = "female"

    # --- "young" keyword (overrides any age comparisons for the 16–24 range) ---
    if _RE_YOUNG.search(q):
        filters["min_age"] = 16
        filters["max_age"] = 24

    # --- Age comparisons (only if "young" didn't already set them) ---
    if "min_age" not in filters:
        m = _RE_MIN_AGE.search(q)
        if m:
            filters["min_age"] = int(m.group(1))

    if "max_age" not in filters:
        m = _RE_MAX_AGE.search(q)
        if m:
            filters["max_age"] = int(m.group(1))

    # --- Age groups ---
    # Only one age_group can be active; last match wins (patterns are mutually
    # exclusive in practice, but we apply them in specificity order).
    if _RE_CHILD.search(q):
        filters["age_group"] = "child"
    if _RE_TEENAGER.search(q):
        filters["age_group"] = "teenager"
    if _RE_ADULT.search(q):
        filters["age_group"] = "adult"
    if _RE_SENIOR.search(q):
        filters["age_group"] = "senior"

    # --- Country ---
    m = _RE_COUNTRY.search(q)
    if m:
        country_code = _resolve_country(m.group(1))
        if country_code:
            filters["country_id"] = country_code

    # --- Guard: nothing was recognised ---
    if not filters:
        raise UninterpretableQueryError(
            f"Unable to interpret query: {q!r}"
        )

    return filters
