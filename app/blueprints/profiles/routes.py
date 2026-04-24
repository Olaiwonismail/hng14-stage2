from flask import jsonify, request, current_app
from sqlalchemy.exc import OperationalError

from app.blueprints.profiles import profiles_bp
from app.blueprints.profiles.validator import validate_params
from app.db.queries import build_profile_query
from app.extensions import get_engine
from app.serialisers import serialise_profile


@profiles_bp.route("/profiles", methods=["GET"])
def get_profiles():
    # 1. Validate and coerce query params
    params = validate_params(request.args)

    # 2. Build filter dict from FilterParams
    filters = {
        "gender": params.gender,
        "age_group": params.age_group,
        "country_id": params.country_id,
        "min_age": params.min_age,
        "max_age": params.max_age,
        "min_gender_probability": params.min_gender_probability,
        "min_country_probability": params.min_country_probability,
    }

    # 3. Build queries
    data_query, count_query = build_profile_query(
        filters=filters,
        sort_by=params.sort_by,
        order=params.order,
        page=params.page,
        limit=params.limit,
    )

    # 4. Execute queries
    try:
        engine = get_engine(current_app)
        with engine.connect() as conn:
            rows = conn.execute(data_query).mappings().all()
            total = conn.execute(count_query).scalar()
    except OperationalError as e:
        from flask import abort
        abort(502, description="Server failure")

    # 5. Serialise and return
    data = [serialise_profile(row) for row in rows]

    return jsonify({
        "status": "success",
        "page": params.page,
        "limit": params.limit,
        "total": total,
        "data": data,
    }), 200
