# Intelligence Query Engine API

A Flask-based REST API for querying demographic profile data with advanced filtering, sorting, pagination, and natural language search capabilities.

## 🚀 Quick Start

```bash
# Clone and setup
git clone <your-repo-url>
cd intelligence-query-engine
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure database
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# Seed database
python scripts/seed.py

# Run server
python run.py
```

API available at: `http://127.0.0.1:5000`

---

## 📋 Table of Contents

- [Features](#features)
- [API Endpoints](#api-endpoints)
- [Natural Language Parser](#natural-language-parser)
- [Setup Guide](#setup-guide)
- [Testing](#testing)
- [Deployment](#deployment)

---

## ✨ Features

- **Advanced Filtering** — 7 filter parameters (gender, age_group, country_id, min/max age, probability thresholds)
- **Natural Language Search** — Plain English queries like "young males from nigeria"
- **Sorting & Pagination** — Sort by age, created_at, or gender_probability; paginate with page/limit
- **CORS Enabled** — `Access-Control-Allow-Origin: *` on all routes
- **Idempotent Seeding** — Load 2026 profiles safely (re-runs skip duplicates)
- **UUID v7** — Time-ordered unique identifiers for all profiles
- **PostgreSQL Backend** — Indexed queries, CHECK constraints, parameterized statements

---

## 🛠 Tech Stack

```
Flask 3.x + SQLAlchemy Core + PostgreSQL 15+
├── flask-cors (CORS middleware)
├── uuid-utils (UUID v7 generation)
├── psycopg2-binary (PostgreSQL adapter)
└── pytest + hypothesis (testing)
```

---

## 🔧 Setup Guide

### Prerequisites

- Python 3.10+
- PostgreSQL 15+

### Installation

```bash
# 1. Clone repository
git clone <your-repo-url>
cd intelligence-query-engine

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
```

### Database Configuration

Edit `.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/insighta_dev
TEST_DATABASE_URL=postgresql://user:password@localhost:5432/insighta_test
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
```

### Seed Database

```bash
python scripts/seed.py
```

**Expected output:**
```
2024-04-24T10:30:00 [INFO] Loaded 2026 profiles from data/profiles.json
2024-04-24T10:30:05 [INFO] Seeding complete — inserted: 2026, skipped: 0
```

Re-running is safe — duplicates are skipped automatically.

### Run Server

```bash
# Development
python run.py

# Or using Flask CLI
flask run

# Production (with Gunicorn)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

Server runs at: `http://127.0.0.1:5000`

### Verify Installation

```bash
# Test profiles endpoint
curl "http://127.0.0.1:5000/api/profiles?limit=5"

# Test search endpoint
curl "http://127.0.0.1:5000/api/profiles/search?q=young+males"
```

---

## 📡 API Endpoints

### Base URL
```
http://127.0.0.1:5000/api
```

All responses include `Access-Control-Allow-Origin: *`

---

### **GET /api/profiles**

Retrieve profiles with filtering, sorting, and pagination.

#### Query Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `gender` | string | `male` or `female` | — |
| `age_group` | string | `child`, `teenager`, `adult`, `senior` | — |
| `country_id` | string | ISO alpha-2 code (case-insensitive) | — |
| `min_age` | integer | Minimum age (inclusive) | — |
| `max_age` | integer | Maximum age (inclusive) | — |
| `min_gender_probability` | float | Min confidence score | — |
| `min_country_probability` | float | Min confidence score | — |
| `sort_by` | string | `age`, `created_at`, `gender_probability` | `created_at` |
| `order` | string | `asc` or `desc` | `desc` |
| `page` | integer | Page number (≥ 1) | `1` |
| `limit` | integer | Results per page (1–50) | `10` |

#### Example Request

```bash
curl "http://127.0.0.1:5000/api/profiles?gender=male&country_id=NG&min_age=25&sort_by=age&order=desc&limit=10"
```

#### Success Response (200)

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

#### Error Responses

- **400** — Invalid query parameters
- **422** — Invalid parameter type
- **500/502** — Server failure

---

### **GET /api/profiles/search**

Search profiles using plain English queries.

#### Query Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `q` | string | Plain-English query | ✅ Yes |
| `page` | integer | Page number | No |
| `limit` | integer | Results per page (1–50) | No |

#### Example Request

```bash
curl "http://127.0.0.1:5000/api/profiles/search?q=young+males+from+nigeria"
```

#### Success Response (200)

Same structure as `/api/profiles`

#### Error Responses

- **400** — Missing/empty `q` or uninterpretable query
- **422** — Invalid `page`/`limit` type
- **500/502** — Server failure

---

## 🧠 Natural Language Parser

The NL parser converts plain English queries into structured filters using **rule-based pattern matching** (no AI/LLMs).

### Supported Keywords

| Keyword/Phrase | Mapped Filter(s) |
|----------------|------------------|
| `young` | `min_age=16`, `max_age=24` |
| `male` / `males` | `gender=male` |
| `female` / `females` | `gender=female` |
| `male and female` | *(gender filter omitted)* |
| `above N` / `over N` / `older than N` | `min_age=N` |
| `below N` / `under N` / `younger than N` | `max_age=N` |
| `child` / `children` | `age_group=child` |
| `teenager` / `teen` | `age_group=teenager` |
| `adult` / `adults` | `age_group=adult` |
| `senior` / `elderly` | `age_group=senior` |
| `from <country>` / `in <country>` | `country_id=<ISO code>` |

### Example Queries

```bash
# Young males
?q=young+males
→ gender=male, min_age=16, max_age=24

# Females above 30
?q=females+above+30
→ gender=female, min_age=30

# Adult males from Kenya
?q=adult+males+from+kenya
→ gender=male, age_group=adult, country_id=KE

# Male and female teenagers above 17
?q=male+and+female+teenagers+above+17
→ age_group=teenager, min_age=17 (gender omitted)
```

### How It Works

1. **Multiple keywords** are combined with **AND logic**
2. **65 countries** supported (Nigeria, Kenya, Ghana, South Africa, etc.)
3. **Case-insensitive** matching
4. **Unrecognized queries** return `400` with `"Unable to interpret query"`

### Limitations

❌ **Not supported:**
- OR logic ("males or females")
- Negation ("not from nigeria")
- Complex ranges ("between 20 and 30")
- Fuzzy country names (must match country map)

✅ **Workarounds:**
- Use `/api/profiles` with direct filter params for unsupported patterns
- Make multiple API calls and merge results client-side for OR logic

---

## 🧪 Testing

### Run All Tests

```bash
pytest tests/
```

### Run Unit Tests Only

```bash
pytest tests/unit/ -v
```

### Run Integration Tests Only

```bash
pytest tests/integration/ -v
```

**Note:** Integration tests require PostgreSQL. Set `TEST_DATABASE_URL` in `.env`

### Test Coverage

- **45 unit tests** — NL parser, serialiser, validator
- **Integration tests** — Profiles endpoint, search endpoint, CORS, error handling
- **Property-based tests** — Hypothesis-powered (100 iterations per test)

---

## 🚀 Deployment

### Supported Platforms

✅ **Vercel** | **Railway** | **Heroku** | **AWS** | **PXXL App**  
❌ **Render** (not accepted per requirements)

### Environment Variables

```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
SECRET_KEY=<generate-with-secrets.token_hex(32)>
FLASK_ENV=production
```

### Pre-Deployment Checklist

- [ ] Set up production PostgreSQL database
- [ ] Configure environment variables
- [ ] Run seeder: `python scripts/seed.py`
- [ ] Verify 2026 profiles loaded
- [ ] Test both endpoints from multiple networks
- [ ] Confirm CORS headers present

### Production Server

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

---

## 📁 Project Structure

```
intelligence-query-engine/
├── app/
│   ├── __init__.py          # Application factory
│   ├── config.py            # Config classes
│   ├── extensions.py        # SQLAlchemy engine
│   ├── serialisers.py       # JSON serialisation
│   ├── blueprints/
│   │   ├── profiles/        # GET /api/profiles
│   │   └── search/          # GET /api/profiles/search
│   ├── db/
│   │   ├── schema.py        # Table definitions
│   │   └── queries.py       # Query builder
│   └── nl_parser/
│       ├── parser.py        # NL → filters
│       └── country_map.py   # Country lookup
├── scripts/
│   └── seed.py              # Database seeder
├── tests/
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── data/
│   └── profiles.json        # 2026 profiles
├── .env.example
├── requirements.txt
└── README.md
```

---

## 📝 License

MIT

---

## 🤝 Contributing

Built for **HNG Stage 2 Backend Challenge** — Insighta Labs Intelligence Query Engine

For questions or issues, open a GitHub issue.
#   h n g 1 4 - s t a g e 2 
 
 