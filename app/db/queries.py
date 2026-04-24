from sqlalchemy import select, func

from app.db.schema import profiles_table

# Map sort_by parameter names to table columns
_SORT_COLUMNS = {
    "age": profiles_table.c.age,
    "created_at": profiles_table.c.created_at,
    "gender_probability": profiles_table.c.gender_probability,
}


def build_profile_query(
    filters: dict,
    sort_by: str = "created_at",
    order: str = "desc",
    page: int = 1,
    limit: int = 10,
) -> tuple:
    """
    Build a pair of SQLAlchemy select statements for profile queries.

    Returns:
        (data_query, count_query) where:
        - data_query includes WHERE, ORDER BY, LIMIT, and OFFSET
        - count_query includes only WHERE (no ORDER BY / LIMIT / OFFSET)
    """
    conditions = []

    # gender — exact match
    gender = filters.get("gender")
    if gender is not None:
        conditions.append(profiles_table.c.gender == gender)

    # age_group — exact match
    age_group = filters.get("age_group")
    if age_group is not None:
        conditions.append(profiles_table.c.age_group == age_group)

    # country_id — case-insensitive match via UPPER()
    country_id = filters.get("country_id")
    if country_id is not None:
        conditions.append(
            func.upper(profiles_table.c.country_id) == country_id.upper()
        )

    # min_age — inclusive lower bound on age
    min_age = filters.get("min_age")
    if min_age is not None:
        conditions.append(profiles_table.c.age >= min_age)

    # max_age — inclusive upper bound on age
    max_age = filters.get("max_age")
    if max_age is not None:
        conditions.append(profiles_table.c.age <= max_age)

    # min_gender_probability — inclusive lower bound
    min_gender_probability = filters.get("min_gender_probability")
    if min_gender_probability is not None:
        conditions.append(
            profiles_table.c.gender_probability >= min_gender_probability
        )

    # min_country_probability — inclusive lower bound
    min_country_probability = filters.get("min_country_probability")
    if min_country_probability is not None:
        conditions.append(
            profiles_table.c.country_probability >= min_country_probability
        )

    # Resolve sort column (default to created_at if unknown)
    sort_col = _SORT_COLUMNS.get(sort_by, profiles_table.c.created_at)
    order_expr = sort_col.asc() if order == "asc" else sort_col.desc()

    # Pagination
    offset = (page - 1) * limit

    # Data query: full select with ordering and pagination
    data_query = (
        select(profiles_table)
        .where(*conditions)
        .order_by(order_expr)
        .limit(limit)
        .offset(offset)
    )

    # Count query: same WHERE clauses, no ordering or pagination
    count_query = (
        select(func.count())
        .select_from(profiles_table)
        .where(*conditions)
    )

    return data_query, count_query
