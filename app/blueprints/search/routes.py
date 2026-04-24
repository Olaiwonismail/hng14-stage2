"""
GET /api/profiles/search — natural language profile search endpoint.

Accepts a plain-English ``q`` parameter, parses it into structured filters
using the rule-based NL parser, then delegates to the same query builder
and serialiser used by the profiles endpoint.
"""

from __future__ import annotations

from flask import jsonify, request, current_app
from sqlalchemy.exc import OperationalError

from app.blueprints.search import search_bp
from app.db.queries import build_profile_query
from app.extensions import get_engine
from app.nl_parser.parser import UninterpretableQueryError, parse_query
from app.serialisers import serialise_profile

# Pagination params accepted on the search endpoint
_PAGINATION_PARAMS = frozenset({"page", "limit"})


def _get_pagination(args) -> tuple[int, int]:
    """Extract and validate page/limit from request args.

    Returns (page, limit) with defaults applied.
    Aborts with 422 on non-integer values, 400 if limit > 50 or page < 1.
    """
    from flask import abort

    page = 1
    limit = 10

    if "page" in args:
        try:
            page = int(args["page"])
        except ValueError:
            abort(422, description="Invalid parameter type")
        if page < 1:
            abort(400, description="Invalid query parameters")

    if "limit" in args:
        try:
            limit = int(args["limit"])
        except ValueError:
            abort(422, description="Invalid parameter type")
        if limit > 50:
            abort(400, description="Invalid query parameters")

    return page, limit


@search_bp.route("/profiles/search", methods=["GET"])
def search_profiles():
    from flask import abort

    # 1. Require a non-empty `q` parameter
    q = request.args.get("q", "").strip()
    if not q:
        return (
            jsonify({"status": "error", "message": "Missing or empty parameter"}),
            400,
        )

    # 2. Parse the natural language query
    try:
        filters = parse_query(q)
    except UninterpretableQueryError:
        return (
            jsonify({"status": "error", "message": "Unable to interpret query"}),
            400,
        )

    # 3. Extract pagination params (page, limit only — no other params allowed)
    page, limit = _get_pagination(request.args)

    # 4. Build queries using the resolved filters
    data_query, count_query = build_profile_query(
        filters=filters,
        sort_by="created_at",
        order="desc",
        page=page,
        limit=limit,
    )

    # 5. Execute queries
    try:
        engine = get_engine(current_app)
        with engine.connect() as conn:
            rows = conn.execute(data_query).mappings().all()
            total = conn.execute(count_query).scalar()
    except OperationalError:
        abort(502, description="Server failure")

    # 6. Serialise and return
    data = [serialise_profile(row) for row in rows]

    return jsonify({
        "status": "success",
        "page": page,
        "limit": limit,
        "total": total,
        "data": data,
    }), 200
