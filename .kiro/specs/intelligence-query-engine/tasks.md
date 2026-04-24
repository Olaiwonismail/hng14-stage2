# Implementation Plan: Intelligence Query Engine

## Overview

Implement a Flask 3.x REST API backed by PostgreSQL that exposes two endpoints — `GET /api/profiles` (filterable, sortable, paginated) and `GET /api/profiles/search` (natural-language query) — together with a rule-based NL parser, SQLAlchemy Core query builder, response serialiser, global error handlers, CORS support, an idempotent data seeder, property-based tests (Hypothesis), and a README.

Each task builds incrementally on the previous one. No code is left unintegrated.

---

## Tasks

- [x] 1. Scaffold project structure and pin dependencies
  - Create the directory tree: `app/`, `app/blueprints/profiles/`, `app/blueprints/search/`, `app/db/`, `app/nl_parser/`, `scripts/`, `tests/unit/`, `tests/integration/`, `data/`
  - Create `requirements.txt` with pinned versions: `flask>=3.0`, `flask-cors`, `sqlalchemy>=2.0`, `psycopg2-binary`, `uuid-utils`, `python-dotenv`, `pytest`, `hypothesis`
  - Create `run.py` entry point that calls `create_app()`
  - Create `.env.example` with `DATABASE_URL`, `FLASK_ENV`, and `SECRET_KEY` placeholders
  - Create empty `__init__.py` files for all packages
  - _Requirements: 1.1, 8.3_

- [x] 2. Implement configuration and application factory
  - [x] 2.1 Create `app/config.py` with `Development`, `Testing`, and `Production` config classes; each reads `DATABASE_URL` from the environment
    - `Testing` config sets `TESTING=True` and points to a separate test database URL
    - _Requirements: 1.1_

  - [x] 2.2 Create `app/extensions.py` with `init_db(app)` that initialises a SQLAlchemy `Engine` and stores it on `app.extensions["db_engine"]`
    - Use `create_engine` with a connection pool; expose a `get_engine(app)` helper
    - _Requirements: 8.3_

  - [x] 2.3 Create `app/__init__.py` with `create_app(config_name)` application factory
    - Register `flask-cors` for `r"/api/*"` with `origins="*"`
    - Call `init_db(app)`
    - Register `profiles_bp` and `search_bp` blueprints under `/api`
    - Call `register_error_handlers(app)`
    - _Requirements: 6.1, 6.2_

- [x] 3. Define database schema and create DDL helpers
  - [x] 3.1 Create `app/db/schema.py` with the `profiles_table` SQLAlchemy Core `Table` definition
    - Columns: `id VARCHAR(36) PK`, `name VARCHAR UNIQUE NOT NULL`, `gender VARCHAR NOT NULL`, `gender_probability FLOAT NOT NULL`, `age INTEGER NOT NULL`, `age_group VARCHAR NOT NULL`, `country_id VARCHAR(2) NOT NULL`, `country_name VARCHAR NOT NULL`, `country_probability FLOAT NOT NULL`, `created_at TIMESTAMPTZ DEFAULT NOW()`
    - Constraints: `ck_gender`, `ck_age_group`, `ck_country_id_len`, `uq_name`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

  - [x] 3.2 Add `create_all_tables(engine)` and `drop_all_tables(engine)` helpers in `app/db/schema.py` using `metadata.create_all` / `metadata.drop_all`
    - Also emit the seven performance indexes (`idx_profiles_gender`, `idx_profiles_age_group`, `idx_profiles_country_id`, `idx_profiles_age`, `idx_profiles_gender_probability`, `idx_profiles_country_probability`, `idx_profiles_created_at`) via `DDL` or raw `text()` executed after `create_all`
    - _Requirements: 8.1_

  - [ ]* 3.3 Write property test for gender constraint enforcement
    - **Property 2: Gender constraint enforcement**
    - **Validates: Requirements 1.5**
    - File: `tests/unit/test_schema_constraints.py`
    - Use `@given(st.text().filter(lambda s: s not in {"male", "female"}))` — any non-valid gender string inserted into the table must raise a DB constraint error

  - [ ]* 3.4 Write property test for age_group constraint enforcement
    - **Property 3: Age group constraint enforcement**
    - **Validates: Requirements 1.6**
    - File: `tests/unit/test_schema_constraints.py`
    - Use `@given(st.text().filter(lambda s: s not in {"child","teenager","adult","senior"}))` — any non-valid age_group string must raise a DB constraint error

  - [ ]* 3.5 Write property test for country_id length constraint enforcement
    - **Property 4: Country ID length constraint enforcement**
    - **Validates: Requirements 1.7**
    - File: `tests/unit/test_schema_constraints.py`
    - Use `@given(st.text().filter(lambda s: len(s) != 2))` — any string whose length ≠ 2 must raise a DB constraint error

- [x] 4. Implement SQLAlchemy Core query builder
  - [x] 4.1 Create `app/db/queries.py` with `build_profile_query(filters, sort_by, order, page, limit) -> tuple[Select, Select]`
    - Dynamically append `WHERE` clauses for each non-None filter field using parameterised binds
    - Apply `UPPER(country_id) = UPPER(:country_id)` for case-insensitive country matching
    - Return `(data_query, count_query)` — data query includes `ORDER BY`, `LIMIT`, `OFFSET`; count query wraps in `COUNT(*)`
    - _Requirements: 3.4–3.15, 3.17, 3.18, 8.2, 8.3_

  - [ ]* 4.2 Write unit tests for query builder
    - Verify that each filter field produces the correct SQL clause
    - Verify that `LIMIT`/`OFFSET` values are computed correctly from `page` and `limit`
    - Verify that `ORDER BY` direction matches the `order` parameter
    - _Requirements: 3.13, 3.15, 8.3_

- [x] 5. Implement response serialiser
  - Create `app/serialisers.py` with `serialise_profile(row: RowMapping) -> dict`
  - Format `created_at` as `"%Y-%m-%dT%H:%M:%SZ"` (UTC ISO 8601)
  - Cast `id` to `str`
  - _Requirements: 7.1, 7.2_

  - [ ]* 5.1 Write unit tests for serialiser
    - Test that `created_at` is formatted correctly for a known datetime value
    - Test that `id` is returned as a string
    - _Requirements: 7.1, 7.2_

- [x] 6. Implement query parameter validator
  - [x] 6.1 Create `app/blueprints/profiles/validator.py` with the `FilterParams` dataclass and `validate_params(args: MultiDict) -> FilterParams`
    - Define `ALLOWED_PARAMS`, `VALID_GENDERS`, `VALID_AGE_GROUPS`, `VALID_SORT_BY`, `VALID_ORDERS` constants
    - Validation order: (1) unknown param names → `abort(400)`; (2) coerce numeric types → `abort(422)` on failure; (3) validate enum values → `abort(400)`; (4) validate `limit <= 50` → `abort(400)`; (5) apply defaults (`page=1`, `limit=10`, `sort_by="created_at"`, `order="desc"`)
    - _Requirements: 3.3, 3.13, 3.14, 3.15, 3.16, 5.1–5.6_

  - [ ]* 6.2 Write property test for invalid numeric type → 422
    - **Property 13: Input validation — invalid parameter types return 422**
    - **Validates: Requirements 5.1**
    - File: `tests/unit/test_validator.py`
    - Use `@given(st.text().filter(lambda s: not s.lstrip("-").isdigit()))` for `min_age` and `max_age`; assert `abort(422)` is raised

  - [ ]* 6.3 Write property test for invalid enum values → 400
    - **Property 14: Input validation — invalid enum values return 400**
    - **Validates: Requirements 5.3, 5.4, 5.5, 5.6**
    - File: `tests/unit/test_validator.py`
    - Use `@given(st.text().filter(lambda s: s not in VALID_GENDERS))` for `gender`; assert `abort(400)` is raised; repeat for `age_group`, `sort_by`, `order`

  - [ ]* 6.4 Write unit tests for validator
    - Test that valid params parse correctly and defaults are applied
    - Test that unknown param names return 400
    - Test that `limit > 50` returns 400
    - _Requirements: 3.3, 3.14, 3.15, 3.16, 5.2_

- [x] 7. Implement `GET /api/profiles` endpoint
  - [x] 7.1 Create `app/blueprints/profiles/__init__.py` defining `profiles_bp = Blueprint("profiles", __name__)`
    - _Requirements: 3.1_

  - [x] 7.2 Create `app/blueprints/profiles/routes.py` with the `GET /profiles` route handler
    - Call `validate_params(request.args)` to get a `FilterParams` instance
    - Call `build_profile_query(...)` to get `(data_query, count_query)`
    - Execute both queries using a connection from `get_engine(current_app)`
    - Serialise each row with `serialise_profile`
    - Return `jsonify({"status": "success", "page": ..., "limit": ..., "total": ..., "data": [...]})`
    - Catch `OperationalError` and re-raise as HTTP 502
    - _Requirements: 3.1, 3.2, 3.3, 3.4–3.18, 7.3, 7.4, 5.7, 5.8_

- [x] 8. Checkpoint — profiles endpoint smoke test
  - Ensure all tests written so far pass
  - Manually verify (or via a smoke-test fixture) that `GET /api/profiles` returns the expected JSON structure with default params
  - Ask the user if any questions arise before continuing

- [x] 9. Implement NL Parser
  - [x] 9.1 Create `app/nl_parser/country_map.py` with the `COUNTRY_MAP: dict[str, str]` static lookup table
    - Map lowercase country names to ISO alpha-2 codes; include all countries present in `seed_profiles.json`
    - _Requirements: 4.9_

  - [x] 9.2 Create `app/nl_parser/parser.py` with `parse_query(q: str) -> dict` pure function
    - Define `UninterpretableQueryError` exception class
    - Apply regex rules in order (case-insensitive): `young` → `min_age=16, max_age=24`; `males?` → `gender=male`; `females?` → `gender=female`; both male+female → omit gender; `above N` → `min_age=N`; `below N` → `max_age=N`; `from <country>` → `country_id` via `COUNTRY_MAP`; age group keywords → `age_group`
    - Raise `UninterpretableQueryError` if `q` is non-empty but no patterns match
    - _Requirements: 4.3–4.12_

  - [ ]* 9.3 Write property test for NL Parser keyword-to-filter mapping
    - **Property 10: NL Parser — keyword-to-filter mapping**
    - **Validates: Requirements 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 4.10**
    - File: `tests/unit/test_nl_parser.py`
    - Use `@given(st.text())` with strategies that embed recognised keywords; assert the correct filter key and value appear in the output dict

  - [ ]* 9.4 Write property test for NL Parser multi-keyword conjunction
    - **Property 11: NL Parser — multi-keyword conjunction**
    - **Validates: Requirements 4.12**
    - File: `tests/unit/test_nl_parser.py`
    - Use `@given(st.lists(st.sampled_from(KEYWORD_LIST), min_size=2))` — for any combination of keywords, all resolved filters must be present in the output dict

  - [ ]* 9.5 Write unit tests for NL Parser
    - Test `"male and female"` omits gender filter (Req 4.11)
    - Test empty `q` raises `UninterpretableQueryError` (Req 4.17)
    - Test unrecognised `q` raises `UninterpretableQueryError` (Req 4.17)
    - Test `"young"` maps to `min_age=16, max_age=24` (Req 4.4)
    - _Requirements: 4.4–4.12, 4.16, 4.17_

- [x] 10. Implement `GET /api/profiles/search` endpoint
  - [x] 10.1 Create `app/blueprints/search/__init__.py` defining `search_bp = Blueprint("search", __name__)`
    - _Requirements: 4.1_

  - [x] 10.2 Create `app/blueprints/search/routes.py` with the `GET /profiles/search` route handler
    - Return 400 `{"status":"error","message":"Missing or empty parameter"}` if `q` is absent or empty
    - Call `parse_query(q)`; catch `UninterpretableQueryError` and return 400 `{"status":"error","message":"Unable to interpret query"}`
    - Pass resolved filters through `validate_params` (pagination only) and `build_profile_query`
    - Serialise and return the same response structure as the profiles endpoint
    - _Requirements: 4.1, 4.2, 4.13, 4.14, 4.15, 4.16, 4.17_

- [x] 11. Implement global error handlers
  - Create `register_error_handlers(app)` function (can live in `app/__init__.py` or a dedicated `app/errors.py`)
  - Register handlers for 400, 422, 500, and 502 returning `{"status": "error", "message": "..."}` JSON
  - _Requirements: 5.7, 5.8, 7.3_

- [x] 12. Implement idempotent data seeder
  - [x] 12.1 Copy `seed_profiles.json` from the workspace root into `data/profiles.json`
    - _Requirements: 2.1_

  - [x] 12.2 Create `scripts/seed.py` standalone script
    - Read `data/profiles.json`; exit with a descriptive error log if the file is missing or unreadable (Req 2.5)
    - For each record, generate a UUID v7 with `uuid_utils.uuid7()`
    - Derive `age_group` from `age` if not already present in the JSON
    - Insert in batches using `INSERT INTO profiles ... ON CONFLICT (name) DO NOTHING`
    - Log total inserted vs skipped counts to stdout
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 1.4_

  - [ ]* 12.3 Write property test for seeder idempotency
    - **Property 5: Seeder idempotency**
    - **Validates: Requirements 2.2**
    - File: `tests/unit/test_schema_constraints.py` (or a dedicated `tests/integration/test_seeder.py`)
    - Run the seeder twice against the test DB; assert `COUNT(*)` after the second run equals `COUNT(*)` after the first run

  - [ ]* 12.4 Write property test for UUID v7 validity
    - **Property 1: UUID v7 validity for all inserted profiles**
    - **Validates: Requirements 1.4, 2.4**
    - File: `tests/unit/test_schema_constraints.py`
    - For any profile inserted by the seeder, assert `id` is a 36-character hyphenated hex string whose version nibble is `7`

- [x] 13. Set up pytest fixtures and Hypothesis configuration
  - Create `tests/conftest.py` with session-scoped `app` fixture (`create_app("testing")`), `create_all_tables` / `drop_all_tables` setup/teardown, and a `client` fixture
  - Add Hypothesis CI profile: `settings.register_profile("ci", max_examples=100, suppress_health_check=[HealthCheck.too_slow])` and `settings.load_profile("ci")`
  - _Requirements: (testing infrastructure)_

- [x] 14. Write integration tests for `GET /api/profiles`
  - [x] 14.1 Write example-based integration tests in `tests/integration/test_profiles_endpoint.py`
    - Default params return 10 results ordered by `created_at` desc
    - `limit > 50` returns 400
    - OPTIONS request returns 200 with CORS headers
    - Unknown param returns 400
    - _Requirements: 3.2, 3.3, 3.16, 6.1, 6.2, 5.2_

  - [ ]* 14.2 Write property test for response structure invariant
    - **Property 6: Response structure invariant**
    - **Validates: Requirements 3.2, 4.15, 7.4**
    - Use `@given(valid_filter_params())` — every valid request must return a response with exactly `status`, `page`, `limit`, `total`, `data` where `status="success"`, `page` and `limit` are positive integers, `total` ≥ 0, and `data` is a list

  - [ ]* 14.3 Write property test for filter correctness
    - **Property 7: Filter correctness — all returned profiles satisfy applied filters**
    - **Validates: Requirements 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12**
    - Use `@given(valid_filter_params())` — every profile in `data` must satisfy all applied filter conditions simultaneously

  - [ ]* 14.4 Write property test for sort order correctness
    - **Property 8: Sort order correctness**
    - **Validates: Requirements 3.13**
    - Use `@given(st.sampled_from(SORT_FIELDS), st.sampled_from(ORDERS))` — consecutive pairs in `data` must satisfy the specified ordering relation

  - [ ]* 14.5 Write property test for pagination consistency
    - **Property 9: Pagination consistency**
    - **Validates: Requirements 3.15, 3.17**
    - Use `@given(st.integers(1, 10), st.integers(1, 50))` — `len(data) <= limit` and `total` equals a direct `COUNT(*)` with the same filters

  - [ ]* 14.6 Write property test for CORS header on all API responses
    - **Property 15: CORS header on all API responses**
    - **Validates: Requirements 6.1**
    - Use `@given(valid_filter_params())` — every response must include `Access-Control-Allow-Origin: *`

  - [ ]* 14.7 Write property test for timestamp format invariant
    - **Property 16: Timestamp format invariant**
    - **Validates: Requirements 7.1**
    - Use `@given(valid_filter_params())` — every `created_at` value in `data` must match `YYYY-MM-DDTHH:MM:SSZ`

  - [ ]* 14.8 Write property test for error response structure invariant
    - **Property 17: Error response structure invariant**
    - **Validates: Requirements 5.1–5.8, 7.3**
    - Use `@given(invalid_params())` — every error response must contain exactly `status="error"` and a non-empty `message` string

- [ ] 15. Write integration tests for `GET /api/profiles/search`
  - [x] 15.1 Write example-based integration tests in `tests/integration/test_search_endpoint.py`
    - Missing `q` returns 400 with `"Missing or empty parameter"`
    - Unrecognised `q` returns 400 with `"Unable to interpret query"`
    - Multi-keyword query applies AND logic and returns correct results
    - _Requirements: 4.13, 4.16, 4.17_

  - [ ]* 15.2 Write property test for search endpoint filter equivalence
    - **Property 12: Search endpoint filter equivalence**
    - **Validates: Requirements 4.13**
    - Use `@given(interpretable_query_strings())` — `GET /api/profiles/search?q=<q>` must return the same `total` and profile IDs as `GET /api/profiles` with the equivalent filter params applied directly

- [x] 16. Checkpoint — full test suite
  - Run `pytest tests/` and ensure all non-optional tests pass
  - Fix any failures before proceeding
  - Ask the user if any questions arise

- [x] 17. Write README
  - Create `README.md` at the project root with:
    - Project overview and architecture summary
    - Setup and run instructions (virtualenv, `pip install -r requirements.txt`, `.env` configuration, running the seeder, starting the server)
    - NL Parser section: all supported keywords/phrases and their filter mappings, how multiple keywords are combined (AND logic), known limitations and unhandled edge cases
    - Example `q` values and their resolved filter outputs
    - API reference for both endpoints (parameters, defaults, error codes)
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [x] 18. Final checkpoint — wire everything together
  - Verify `run.py` starts the app cleanly with `flask run`
  - Verify the seeder script runs end-to-end against a local DB and loads 2026 records
  - Verify `GET /api/profiles` and `GET /api/profiles/search` return correct responses
  - Run `pytest tests/` one final time; ensure all non-optional tests pass
  - Ask the user if any questions arise

---

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Checkpoints (tasks 8, 16, 18) ensure incremental validation
- Property tests validate universal correctness properties; unit/integration tests validate specific examples and edge cases
- The seeder reads from `data/profiles.json` (copied from `seed_profiles.json` in the workspace root)
- All database interactions use parameterised queries via SQLAlchemy Core to prevent SQL injection (Req 8.3)
