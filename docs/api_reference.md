# API reference

Base URL: `http://localhost:8000` · Prefix: `/api/v1`

## Auth

### `POST /api/v1/auth/register`

```json
{ "email": "ada@uni.edu", "password": "password123", "full_name": "Ada Lovelace" }
```

Returns `{ access_token, token_type, user }`.

### `POST /api/v1/auth/login`

OAuth2 password form: `username=<email>&password=<password>`.

### `GET /api/v1/auth/me`

Header: `Authorization: Bearer <token>`.

## Analyze

### `POST /api/v1/analyze` (multipart)

| Field | Required | Notes |
|-------|----------|-------|
| `file` | yes | PDF |
| `name` | yes | Display name |
| `extra_skills` | no | Comma-separated |
| `role_id` | one of role/JD | Sample role |
| `job_description` | one of role/JD | Free text |
| `location` | no | Improves location gate |
| `cgpa` | no | 4.0-scale number |

Auth optional; if present, analysis is persisted.

### `POST /api/v1/what-if`

JSON body with `current_skills`, `add_skills`, `job_skills`, profile counts, and `eligible`.

### `GET /api/v1/analyses/mine`

Requires auth — last 50 analyses for the user.

## Catalog & job feed

- `GET /api/v1/roles`
- `GET /api/v1/roles/{id}`
- `GET /api/v1/sample-jds/{id}`
- `GET /api/v1/jobs/feed?level=all|entry|mid|senior&source=all|curated|live&refresh=false`
- `GET /api/v1/jobs/{job_id}`

The feed merges curated market-style JDs for **entry / mid / senior** with a Remotive remote-jobs cache. `refresh=true` attempts a live Remotive pull (falls back to cache if blocked).

## Admin (admin JWT required)

- `GET /api/v1/admin/stats`
- `GET /api/v1/admin/users`
- `PATCH /api/v1/admin/users/{id}/toggle-active`
- `GET /api/v1/admin/analyses`

## Example curl

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin@example.com&password=Admin@Arawind2026" | jq -r .access_token)

curl -s -X POST http://localhost:8000/api/v1/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@docs/sample_resume.pdf" \
  -F "name=Alex Rivera" \
  -F "role_id=ml-engineer" \
  -F "location=Bangalore" \
  -F "cgpa=3.2"
```
