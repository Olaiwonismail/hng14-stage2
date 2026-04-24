from dataclasses import dataclass
from flask import abort

ALLOWED_PARAMS = frozenset({
    "gender", "age_group", "country_id",
    "min_age", "max_age", "min_gender_probability", "min_country_probability",
    "sort_by", "order", "page", "limit",
})

VALID_GENDERS = frozenset({"male", "female"})
VALID_AGE_GROUPS = frozenset({"child", "teenager", "adult", "senior"})
VALID_SORT_BY = frozenset({"age", "created_at", "gender_probability"})
VALID_ORDERS = frozenset({"asc", "desc"})


@dataclass
class FilterParams:
    gender: str | None = None
    age_group: str | None = None
    country_id: str | None = None
    min_age: int | None = None
    max_age: int | None = None
    min_gender_probability: float | None = None
    min_country_probability: float | None = None
    sort_by: str = "created_at"
    order: str = "desc"
    page: int = 1
    limit: int = 10


def validate_params(args) -> FilterParams:
    """
    Validate and coerce Flask request.args (ImmutableMultiDict) into a FilterParams instance.

    Validation order:
    1. Unknown param names → abort(400)
    2. Coerce numeric types → abort(422) on failure
    3. Validate enum values → abort(400)
    4. Validate limit <= 50 and page >= 1 → abort(400)
    5. Apply defaults and return FilterParams
    """
    # Step 1 — Unknown param names
    for key in args.keys():
        if key not in ALLOWED_PARAMS:
            abort(400, description="Invalid query parameters")

    # Step 2 — Coerce numeric types
    min_age = None
    if "min_age" in args:
        try:
            min_age = int(args["min_age"])
        except ValueError:
            abort(422, description="Invalid parameter type")

    max_age = None
    if "max_age" in args:
        try:
            max_age = int(args["max_age"])
        except ValueError:
            abort(422, description="Invalid parameter type")

    page = None
    if "page" in args:
        try:
            page = int(args["page"])
        except ValueError:
            abort(422, description="Invalid parameter type")

    min_gender_probability = None
    if "min_gender_probability" in args:
        try:
            min_gender_probability = float(args["min_gender_probability"])
        except ValueError:
            abort(422, description="Invalid parameter type")

    min_country_probability = None
    if "min_country_probability" in args:
        try:
            min_country_probability = float(args["min_country_probability"])
        except ValueError:
            abort(422, description="Invalid parameter type")

    limit = None
    if "limit" in args:
        try:
            limit = int(args["limit"])
        except ValueError:
            abort(422, description="Invalid parameter type")

    # Step 3 — Validate enum values
    gender = args.get("gender")
    if gender is not None and gender not in VALID_GENDERS:
        abort(400, description="Invalid query parameters")

    age_group = args.get("age_group")
    if age_group is not None and age_group not in VALID_AGE_GROUPS:
        abort(400, description="Invalid query parameters")

    sort_by = args.get("sort_by")
    if sort_by is not None and sort_by not in VALID_SORT_BY:
        abort(400, description="Invalid query parameters")

    order = args.get("order")
    if order is not None and order not in VALID_ORDERS:
        abort(400, description="Invalid query parameters")

    # Step 4 — Validate limit and page
    if limit is not None and limit > 50:
        abort(400, description="Invalid query parameters")

    if page is not None and page < 1:
        abort(400, description="Invalid query parameters")

    # Step 5 — Apply defaults and return FilterParams
    return FilterParams(
        gender=gender,
        age_group=age_group,
        country_id=args.get("country_id"),
        min_age=min_age,
        max_age=max_age,
        min_gender_probability=min_gender_probability,
        min_country_probability=min_country_probability,
        sort_by=sort_by if sort_by is not None else "created_at",
        order=order if order is not None else "desc",
        page=page if page is not None else 1,
        limit=limit if limit is not None else 10,
    )
