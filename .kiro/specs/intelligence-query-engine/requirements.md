# Requirements Document

## Introduction

The Intelligence Query Engine is a backend feature for Insighta Labs, a demographic intelligence company. The system stores demographic profile data and exposes REST API endpoints that allow clients to filter, sort, paginate, and query profiles in plain English. This feature upgrades an existing backend with advanced filtering, sorting, pagination, a natural language search endpoint, and a one-time idempotent data seeding mechanism for 2026 demographic profiles.

## Glossary

- **System**: The Intelligence Query Engine backend service
- **Profile**: A demographic record stored in the database, representing a single person's demographic attributes
- **Profiles_Table**: The database table storing all Profile records with the defined schema
- **Profiles_Endpoint**: The `GET /api/profiles` HTTP endpoint
- **Search_Endpoint**: The `GET /api/profiles/search` HTTP endpoint
- **NL_Parser**: The rule-based natural language parser that interprets plain-English queries into structured filter parameters
- **Seeder**: The database seeding component responsible for loading profiles from a JSON file
- **Filter**: A query parameter that restricts the set of returned profiles
- **Pagination**: The mechanism for returning a subset of results defined by `page` and `limit` parameters
- **UUID_v7**: A time-ordered universally unique identifier conforming to the UUID version 7 specification
- **age_group**: A categorical classification of age: `child`, `teenager`, `adult`, or `senior`
- **country_id**: A two-character ISO 3166-1 alpha-2 country code (e.g., `NG`, `BJ`, `KE`, `AO`)
- **UTC_ISO_8601**: Timestamps formatted as ISO 8601 strings in the UTC timezone (e.g., `2024-01-15T10:30:00Z`)

---

## Requirements

### Requirement 1: Database Schema

**User Story:** As a system administrator, I want a well-defined profiles table, so that demographic data is stored consistently and can be queried efficiently.

#### Acceptance Criteria

1. THE Profiles_Table SHALL contain the following columns: `id` (UUID v7, primary key), `name` (VARCHAR, unique), `gender` (VARCHAR), `gender_probability` (FLOAT), `age` (INT), `age_group` (VARCHAR), `country_id` (VARCHAR(2)), `country_name` (VARCHAR), `country_probability` (FLOAT), and `created_at` (TIMESTAMP).
2. THE Profiles_Table SHALL enforce a UNIQUE constraint on the `name` column.
3. THE Profiles_Table SHALL set `created_at` to the current UTC timestamp automatically on row insertion.
4. THE Profiles_Table SHALL store all `id` values as UUID v7 identifiers.
5. THE Profiles_Table SHALL restrict `gender` values to `"male"` or `"female"`.
6. THE Profiles_Table SHALL restrict `age_group` values to `"child"`, `"teenager"`, `"adult"`, or `"senior"`.
7. THE Profiles_Table SHALL restrict `country_id` values to two-character ISO 3166-1 alpha-2 codes.

---

### Requirement 2: Data Seeding

**User Story:** As a system administrator, I want the database seeded with 2026 profiles from a JSON file, so that the system has representative data available from the start.

#### Acceptance Criteria

1. THE Seeder SHALL load exactly 2026 profile records from the provided JSON source file into the Profiles_Table on execution.
2. WHEN the Seeder is executed more than once, THE Seeder SHALL not create duplicate records.
3. WHEN a profile record with the same `name` already exists in the Profiles_Table, THE Seeder SHALL skip that record without raising an error.
4. THE Seeder SHALL assign a valid UUID v7 value to the `id` field of each inserted profile.
5. IF the JSON source file is missing or unreadable, THEN THE Seeder SHALL log a descriptive error message and exit without modifying the database.

---

### Requirement 3: Get All Profiles Endpoint

**User Story:** As a client application, I want to retrieve profiles with filtering, sorting, and pagination, so that I can display relevant demographic data to end users.

#### Acceptance Criteria

1. THE Profiles_Endpoint SHALL accept HTTP GET requests at the path `/api/profiles`.
2. THE Profiles_Endpoint SHALL return a JSON response with the structure `{ "status": "success", "page": <int>, "limit": <int>, "total": <int>, "data": [...] }`.
3. WHEN no query parameters are provided, THE Profiles_Endpoint SHALL return the first 10 profiles ordered by `created_at` descending.
4. THE Profiles_Endpoint SHALL support the following filter parameters: `gender`, `age_group`, `country_id`, `min_age`, `max_age`, `min_gender_probability`, and `min_country_probability`.
5. WHEN the `gender` filter is provided, THE Profiles_Endpoint SHALL return only profiles where `gender` matches the provided value exactly.
6. WHEN the `age_group` filter is provided, THE Profiles_Endpoint SHALL return only profiles where `age_group` matches the provided value exactly.
7. WHEN the `country_id` filter is provided, THE Profiles_Endpoint SHALL return only profiles where `country_id` matches the provided value (case-insensitive).
8. WHEN the `min_age` filter is provided, THE Profiles_Endpoint SHALL return only profiles where `age` is greater than or equal to the provided integer value.
9. WHEN the `max_age` filter is provided, THE Profiles_Endpoint SHALL return only profiles where `age` is less than or equal to the provided integer value.
10. WHEN the `min_gender_probability` filter is provided, THE Profiles_Endpoint SHALL return only profiles where `gender_probability` is greater than or equal to the provided float value.
11. WHEN the `min_country_probability` filter is provided, THE Profiles_Endpoint SHALL return only profiles where `country_probability` is greater than or equal to the provided float value.
12. WHEN multiple filter parameters are provided simultaneously, THE Profiles_Endpoint SHALL apply all filters as a conjunction (AND logic), returning only profiles that satisfy every filter.
13. THE Profiles_Endpoint SHALL support sorting via `sort_by` (accepted values: `age`, `created_at`, `gender_probability`) and `order` (accepted values: `asc`, `desc`).
14. WHEN `sort_by` is provided without `order`, THE Profiles_Endpoint SHALL default to `asc` ordering.
15. THE Profiles_Endpoint SHALL support pagination via `page` (default: 1) and `limit` (default: 10, maximum: 50).
16. WHEN `limit` exceeds 50, THE Profiles_Endpoint SHALL return a 400 error response with `{ "status": "error", "message": "Invalid query parameters" }`.
17. THE Profiles_Endpoint SHALL return the `total` field reflecting the total count of records matching the applied filters, not just the current page count.
18. THE Profiles_Endpoint SHALL use database-level filtering and pagination to avoid full-table scans on filtered queries.

---

### Requirement 4: Natural Language Search Endpoint

**User Story:** As a client application, I want to search profiles using plain English queries, so that non-technical users can find demographic data without knowing filter parameter names.

#### Acceptance Criteria

1. THE Search_Endpoint SHALL accept HTTP GET requests at the path `/api/profiles/search`.
2. THE Search_Endpoint SHALL accept a required query parameter `q` containing a plain-English string.
3. THE NL_Parser SHALL interpret the `q` parameter using rule-based pattern matching without using any AI or large language model services.
4. WHEN the `q` parameter contains the keyword `"young"`, THE NL_Parser SHALL map it to `min_age=16` and `max_age=24`.
5. WHEN the `q` parameter contains the keyword `"male"` or `"males"`, THE NL_Parser SHALL map it to `gender=male`.
6. WHEN the `q` parameter contains the keyword `"female"` or `"females"`, THE NL_Parser SHALL map it to `gender=female`.
7. WHEN the `q` parameter contains the phrase `"above <N>"` where N is an integer, THE NL_Parser SHALL map it to `min_age=N`.
8. WHEN the `q` parameter contains the phrase `"below <N>"` where N is an integer, THE NL_Parser SHALL map it to `max_age=N`.
9. WHEN the `q` parameter contains the phrase `"from <country name>"`, THE NL_Parser SHALL resolve the country name to its ISO 3166-1 alpha-2 `country_id` and apply it as a filter.
10. WHEN the `q` parameter contains an `age_group` keyword (`"child"`, `"children"`, `"teenager"`, `"teenagers"`, `"adult"`, `"adults"`, `"senior"`, `"seniors"`, `"elderly"`), THE NL_Parser SHALL map it to the corresponding `age_group` filter value.
11. WHEN the `q` parameter contains both `"male"` and `"female"` keywords (e.g., `"male and female"`), THE NL_Parser SHALL omit the `gender` filter entirely, returning profiles of all genders.
12. WHEN the `q` parameter contains multiple interpretable keywords, THE NL_Parser SHALL combine all resolved filters as a conjunction (AND logic).
13. THE Search_Endpoint SHALL apply the resolved filters to the Profiles_Table using the same filtering logic as the Profiles_Endpoint.
14. THE Search_Endpoint SHALL support `page` and `limit` pagination parameters with the same defaults and constraints as the Profiles_Endpoint.
15. THE Search_Endpoint SHALL return a response with the same structure as the Profiles_Endpoint: `{ "status": "success", "page": <int>, "limit": <int>, "total": <int>, "data": [...] }`.
16. WHEN the `q` parameter is absent or empty, THE Search_Endpoint SHALL return a 400 error response with `{ "status": "error", "message": "Missing or empty parameter" }`.
17. WHEN the `q` parameter contains no interpretable keywords or patterns, THE Search_Endpoint SHALL return `{ "status": "error", "message": "Unable to interpret query" }`.

---

### Requirement 5: Query Parameter Validation

**User Story:** As a client application, I want clear error responses for invalid inputs, so that I can diagnose and correct integration issues quickly.

#### Acceptance Criteria

1. WHEN a request to the Profiles_Endpoint or Search_Endpoint contains a parameter with an invalid type (e.g., a non-integer value for `min_age`), THE System SHALL return a 422 HTTP response with `{ "status": "error", "message": "Invalid parameter type" }`.
2. WHEN a request to the Profiles_Endpoint contains an unrecognized query parameter name, THE System SHALL return a 400 HTTP response with `{ "status": "error", "message": "Invalid query parameters" }`.
3. WHEN a request to the Profiles_Endpoint contains `sort_by` with a value other than `age`, `created_at`, or `gender_probability`, THE System SHALL return a 400 HTTP response with `{ "status": "error", "message": "Invalid query parameters" }`.
4. WHEN a request to the Profiles_Endpoint contains `order` with a value other than `asc` or `desc`, THE System SHALL return a 400 HTTP response with `{ "status": "error", "message": "Invalid query parameters" }`.
5. WHEN a request to the Profiles_Endpoint contains `gender` with a value other than `"male"` or `"female"`, THE System SHALL return a 400 HTTP response with `{ "status": "error", "message": "Invalid query parameters" }`.
6. WHEN a request to the Profiles_Endpoint contains `age_group` with a value other than `"child"`, `"teenager"`, `"adult"`, or `"senior"`, THE System SHALL return a 400 HTTP response with `{ "status": "error", "message": "Invalid query parameters" }`.
7. WHEN an internal server error occurs, THE System SHALL return a 500 HTTP response with `{ "status": "error", "message": "Server failure" }`.
8. WHEN an upstream dependency is unavailable, THE System SHALL return a 502 HTTP response with `{ "status": "error", "message": "Server failure" }`.

---

### Requirement 6: Cross-Origin Resource Sharing

**User Story:** As a frontend developer, I want the API to allow cross-origin requests, so that browser-based clients can consume the API without CORS errors.

#### Acceptance Criteria

1. THE System SHALL include the HTTP response header `Access-Control-Allow-Origin: *` on all API responses.
2. THE System SHALL handle HTTP OPTIONS preflight requests by returning a 200 response with the appropriate CORS headers.

---

### Requirement 7: Response Format and Timestamps

**User Story:** As a client application, I want consistent response formats and timestamp standards, so that I can reliably parse and display data.

#### Acceptance Criteria

1. THE System SHALL format all `created_at` timestamp values in responses as UTC ISO 8601 strings (e.g., `"2024-01-15T10:30:00Z"`).
2. THE System SHALL return all `id` values in responses as UUID v7 strings.
3. THE System SHALL return all error responses with the structure `{ "status": "error", "message": "<descriptive message>" }`.
4. THE System SHALL return all success responses with the `"status": "success"` field present.

---

### Requirement 8: Performance and Indexing

**User Story:** As a system operator, I want the API to respond efficiently under load, so that clients experience acceptable response times even with large datasets.

#### Acceptance Criteria

1. THE Profiles_Table SHALL have database indexes on the columns `gender`, `age_group`, `country_id`, `age`, `gender_probability`, `country_probability`, and `created_at` to support efficient filtered queries.
2. THE System SHALL use database-level pagination (LIMIT/OFFSET or cursor-based) rather than fetching all records and filtering in application memory.
3. THE System SHALL use parameterized queries for all database interactions to prevent SQL injection.

---

### Requirement 9: README Documentation

**User Story:** As an evaluator or developer, I want a README that explains the natural language parsing approach, so that I can understand the system's capabilities and limitations.

#### Acceptance Criteria

1. THE System SHALL include a README file that describes the natural language parsing approach used by the NL_Parser.
2. THE README SHALL list all supported keywords and phrases and their corresponding filter mappings.
3. THE README SHALL describe how multiple keywords are combined into a single query.
4. THE README SHALL document known limitations and edge cases that the NL_Parser does not handle.
5. THE README SHALL include setup and run instructions for the project.
6. THE README SHALL include example `q` parameter values and their resolved filter outputs.
