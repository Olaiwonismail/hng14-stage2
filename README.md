# Intelligence Query Engine

A Flask-based REST API for querying demographic profile data with advanced filtering, sorting, pagination, and natural language search capabilities.

Built for **Insighta Labs** — a demographic intelligence company serving marketing teams, product teams, and growth analysts.

---

## Features

- **GET /api/profiles** — Filterable, sortable, paginated profile listing
- **GET /api/profiles/search** — Natural language query endpoint (rule-based, no AI/LLMs)
- **Idempotent data seeder** — Load 2026 profiles from JSON with UUID v7 generation
- **PostgreSQL backend** — Robust indexing, CHECK constraints, and parameterized queries
- **CORS enabled** — `Access-Control-Allow-Origin: *` on all `/api/*` routes
- **Property-based testing** — Hypothesis-powered correctness validation

---

## Architecture

```
Flask 3.x (application factory + Blueprints)
├── SQLAlchemy Core (query builder, no ORM)
├── PostgreSQL 15+ (UUID v7, indexes, constraints)
├── flask-cors (CORS middleware)
├── uuid-utils (UUID v7 generation)
└── hypothesis (property-based testing)
```

**Project structure:**

```
intelligence-query-engine/
├── app/
│   ├── __init__.py          # Application factory
│   ├── config.py            # Config classes (Development, Testing, Production)
│   ├── extensions.py        # SQLAlchemy engine init
│   ├── serialisers.py       # Row → JSON conversion
│   ├── blueprints/
│   │   ├── profiles/        # GET /api/profiles
│   │   │   ├── routes.py
│   │   │   └── validator.py
│   │   └── search/          # GET /api/profiles/search
│   │       └── routes.py
│   ├── db/
│   │   ├── schema.py        # Table definitions + DDL helpers
│   │   └── queries.py       # Query builder
│   └── nl_parser/
│       ├── parser.py        # Rule-based NL → filter dict
│       └── country_map.py   # Country name → ISO alpha-2 lookup
├── scripts/
│   └── seed.py              # Idempotent data seeder
├── tests/
│   ├── conftest.py          # pytest fixtures + Hypothesis config
│   ├── unit/
│   │   ├── test_nl_parser.py
│   │   └── test_serialisers.py
│   └── integration/
│       ├── test_profiles_endpoint.py
│       └── test_search_endpoint.py
├── data/
│   └── profiles.json        # Seed data (2026 profiles)
├── .env.example
├── requirements.txt
├── run.py
└── README.md
```

---

## Setup

### Prerequisites

- **Python 3.10+**
- **PostgreSQL 15+** (local or remote)

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd intelligence-query-engine
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and set your database URL:

```bash
cp .env.example .env
```

Edit `.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/insighta_dev
TEST_DATABASE_URL=postgresql://user:password@localhost:5432/insighta_test
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
```

### 5. Seed the database

Run the seeder script to load 2026 profiles:

```bash
python scripts/seed.py
```

**Output:**

```
2024-04-24T10:30:00 [INFO] Loaded 2026 profiles from data/profiles.json
2024-04-24T10:30:05 [INFO] Seeding complete — inserted: 2026, skipped (already existed): 0
```

Re-running the seeder is safe — it uses `INSERT ... ON CONFLICT (name) DO NOTHING` to skip duplicates.

### 6. Start the development server

```bash
python run.py
```

Or use Flask's CLI:

```bash
flask run
```

The API will be available at `http://127.0.0.1:5000`.

---

## API Reference

### Base URL

```
http://127.0.0.1:5000/api
```

All responses include `Access-Control-Allow-Origin: *`.

---

### GET /api/profiles

Retrieve profiles with filtering, sorting, and pagination.

**Query Parameters:**

| Parameter                | Type    | Description                                      | Default      |
|--------------------------|---------|--------------------------------------------------|--------------|
| `gender`                 | string  | Filter by gender (`male` or `female`)            | —            |
| `age_group`              | string  | Filter by age group (`child`, `teenager`, `adult`, `senior`) | — |
| `country_id`             | string  | Filter by ISO alpha-2 country code (case-insensitive) | — |
| `min_age`                | integer | Minimum age (inclusive)                          | —            |
| `max_age`                | integer | Maximum age (inclusive)                          | —            |
| `min_gender_probability` | float   | Minimum gender confidence score                  | —            |
| `min_country_probability`| float   | Minimum country confidence score                 | —            |
| `sort_by`                | string  | Sort field (`age`, `created_at`, `gender_probability`) | `created_at` |
| `order`                  | string  | Sort order (`asc` or `desc`)                     | `desc`       |
| `page`                   | integer | Page number (≥ 1)                                | `1`          |
| `limit`                  | integer | Results per page (1–50)                          | `10`         |

**Example Request:**

```bash
GET /api/profiles?gender=male&country_id=NG&min_age=25&sort_by=age&order=desc&page=1&limit=10
```

**Success Response (200):**

```json
{
  "status": "success",
  "page": 1,
  "limit": 10,
  "total": 2026,
  "data": [
    {
      "id": "018f4e3a-7b2c-7000-8000-000000000001",
      "name": "Amara Osei",
      "gender": "female",
      "gender_probability": 0.97,
      "age": 28,
      "age_group": "adult",
      "country_id": "GH",
      "country_name": "Ghana",
      "country_probability": 0.89,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**Error Responses:**

- **400 Bad Request** — Invalid query parameters (unknown param, invalid enum value, `limit > 50`)
- **422 Unprocessable Entity** — Invalid parameter type (e.g., non-integer `min_age`)
- **500/502 Server Failure** — Database connection error

---

### GET /api/profiles/search

Search profiles using plain English queries.

**Query Parameters:**

| Parameter | Type    | Description                                      | Required |
|-----------|---------|--------------------------------------------------|----------|
| `q`       | string  | Plain-English query string                       | Yes      |
| `page`    | integer | Page number (≥ 1)                                | No       |
| `limit`   | integer | Results per page (1–50)                          | No       |

**Example Request:**

```bash
GET /api/profiles/search?q=young+males+from+nigeria
```

**Success Response (200):**

Same structure as `/api/profiles`.

**Error Responses:**

- **400 Bad Request** — Missing/empty `q`, or uninterpretable query
- **422 Unprocessable Entity** — Invalid `page`/`limit` type
- **500/502 Server Failure** — Database connection error

---

## Natural Language Parser

The NL parser is a **pure function** — it uses **rule-based pattern matching** with no AI or LLM dependencies.

### Supported Keywords and Phrases

| Keyword / Phrase          | Mapped Filter(s)                          |
|---------------------------|-------------------------------------------|
| `young`                   | `min_age=16`, `max_age=24`                |
| `male` / `males`          | `gender=male`                             |
| `female` / `females`      | `gender=female`                           |
| `male and female`         | Gender filter omitted (all genders)       |
| `above N`                 | `min_age=N`                               |
| `below N`                 | `max_age=N`                               |
| `over N`                  | `min_age=N` (alias for "above")           |
| `under N`                 | `max_age=N` (alias for "below")           |
| `older than N`            | `min_age=N`                               |
| `younger than N`          | `max_age=N`                               |
| `child` / `children`      | `age_group=child`                         |
| `teenager` / `teenagers`  | `age_group=teenager`                      |
| `teen` / `teens`          | `age_group=teenager`                      |
| `adult` / `adults`        | `age_group=adult`                         |
| `senior` / `seniors`      | `age_group=senior`                        |
| `elderly`                 | `age_group=senior`                        |
| `from <country name>`     | `country_id=<ISO alpha-2>`                |
| `in <country name>`       | `country_id=<ISO alpha-2>` (alias)        |

### How Multiple Keywords Are Combined

All matched keywords are combined with **AND logic** (conjunction). For example:

- `"young males from nigeria"` → `gender=male AND min_age=16 AND max_age=24 AND country_id=NG`
- `"adult females above 30"` → `gender=female AND age_group=adult AND min_age=30`

### Example Queries and Resolved Filters

| Query                                  | Resolved Filters                                                      |
|----------------------------------------|-----------------------------------------------------------------------|
| `young males`                          | `gender=male`, `min_age=16`, `max_age=24`                             |
| `females above 30`                     | `gender=female`, `min_age=30`                                         |
| `people from angola`                   | `country_id=AO`                                                       |
| `adult males from kenya`               | `gender=male`, `age_group=adult`, `country_id=KE`                     |
| `male and female teenagers above 17`   | `age_group=teenager`, `min_age=17` (gender omitted)                   |
| `seniors from south africa`            | `age_group=senior`, `country_id=ZA`                                   |

### Limitations and Edge Cases

**Not Handled:**

- **OR logic** — "males or females" is not supported; use separate queries
- **Negation** — "not from nigeria" is not supported
- **Ranges with both bounds** — "between 20 and 30" is not supported; use "above 20" or "below 30" separately
- **Fuzzy country names** — Only exact matches (case-insensitive) from the country map are recognized
- **Ambiguous queries** — "young adults" will match both "young" (16–24) and "adult" age group, which may conflict
- **Complex phrases** — "people who are either male or female and above 30" will not parse correctly

**Workarounds:**

- For OR logic, make multiple API calls and merge results client-side
- For ranges, use `min_age` and `max_age` query params directly on `/api/profiles`
- For unsupported countries, use the ISO alpha-2 code directly on `/api/profiles?country_id=XX`

---

## Testing

### Run all tests

```bash
pytest tests/
```

### Run unit tests only

```bash
pytest tests/unit/
```

### Run integration tests only

```bash
pytest tests/integration/
```

**Note:** Integration tests require a PostgreSQL test database. Set `TEST_DATABASE_URL` in your `.env` file.

### Property-Based Testing

The test suite includes Hypothesis-powered property tests that validate universal correctness properties across 100 iterations per test. These are marked as optional in the task list but are included for robustness.

---

## Deployment

### Environment Variables

Set the following in your production environment:

- `DATABASE_URL` — PostgreSQL connection string
- `SECRET_KEY` — Flask secret key (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)
- `FLASK_ENV=production`

### Supported Platforms

- **Vercel** (recommended for Flask apps)
- **Railway**
- **Heroku**
- **AWS Elastic Beanstalk**
- **PXXL App**
- **Any platform supporting Python 3.10+ and PostgreSQL**

**Not supported:** Render (per project requirements)

### Pre-Deployment Checklist

1. Seed the production database: `python scripts/seed.py`
2. Verify all 2026 profiles are loaded
3. Test both endpoints from multiple networks
4. Confirm CORS headers are present on all responses

---

## License

MIT

---

## Contact

For questions or issues, contact the Insighta Labs team.
#   h n g 1 4 - s t a g e 2  
 