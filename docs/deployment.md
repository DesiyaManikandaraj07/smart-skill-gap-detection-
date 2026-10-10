# Deployment guide

## Architecture in Compose

```
frontend (nginx:3000) → backend (uvicorn:8000) → db (postgres:5432)
```

All three services are defined in `docker-compose.yml` with a named volume `pgdata` for persistence.

## Build & run

```bash
cp .env.example .env   # optional; compose embeds defaults
docker compose up --build -d
docker compose ps
curl -s http://localhost:8000/health
```

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `SSG_DATABASE_URL` | Postgres URL in Compose | SQLAlchemy connection |
| `SSG_JWT_SECRET` | demo string | **Must change in production** |
| `SSG_ADMIN_EMAIL` | `admin@example.com` | Seeded admin |
| `SSG_ADMIN_PASSWORD` | `Admin@Arawind2026` | Seeded admin password |
| `SSG_USE_SENTENCE_TRANSFORMERS` | `false` | Enable MiniLM embeddings if installed |
| `SSG_CORS_ORIGINS` | localhost origins | Allowed browser origins |
| `VITE_API_URL` | `http://localhost:8000` | Frontend build-time API base |

## Security checklist (before public exposure)

1. Set a long random `SSG_JWT_SECRET`.
2. Change admin password immediately after first login.
3. Terminate TLS at a reverse proxy (Caddy / Traefik / nginx).
4. Restrict CORS to your real frontend origin.
5. Do not commit `.env` or production secrets.
6. Back up the `pgdata` volume.
7. Remind users: resumes are stored as analysis JSON for signed-in users — disclose in privacy policy.

## Health & ops

```bash
curl http://localhost:8000/health
docker compose logs -f backend
docker compose exec db psql -U arawind -d arawind -c '\dt'
```

## Retraining the model inside the image

The Docker build runs `ml/build_proxy_labels.py` and `ml/train.py`. To refresh:

```bash
docker compose build --no-cache backend
docker compose up -d backend
```

Or mount a host-trained `selection_model.joblib` into `/app/app/models/`.

## Local without Docker

SQLite is the default for laptop demos:

```bash
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev
```

## Known limits

- Resume PDFs are text-layer only (no OCR).
- Proxy labels ≠ real hiring outcomes.
- Frontend `VITE_API_URL` is baked at build time for the nginx image.
