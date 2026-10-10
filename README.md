# Arawind — Smart Skill Gap Detection (v2)

Production-style academic platform that analyzes a student resume against a tech job description, scores **selection likelihood**, enforces **hard eligibility gates** (CGPA, experience, location, degree), and returns a **coaching summary**, skill gaps, roadmap, and what-if simulation.

**Stack:** FastAPI · React · PostgreSQL (Docker) / SQLite (local) · XGBoost / HistGradientBoosting · JWT auth · Admin console

---

## Quick start (Docker — recommended)

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| App UI | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| Health | http://localhost:8000/health |
| Postgres | localhost:5432 (`arawind` / `arawind`) |

### Default admin

- Email: `admin@example.com`
- Password: `Admin@Arawind2026`

Change these via `SSG_ADMIN_EMAIL` / `SSG_ADMIN_PASSWORD` / `SSG_JWT_SECRET` before any real deployment (see `.env.example`).

---

## What the product does

1. **Auth** — email/password register & login (JWT). Analyses are saved when signed in.
2. **Analyze** — PDF resume + **job feed** (entry/mid/senior, curated + Remotive live cache) **or custom JD** (+ optional CGPA & location).
3. **Skills model** — selection likelihood % from a calibrated gradient-boosted model (25k proxy rows with edge cases).
4. **Hard gates** — if CGPA / experience / location / degree fail, **effective** outlook is capped at 0% (real ATS behavior).
5. **Coaching summary** — what the candidate did right, where to improve, critical blockers.
6. **Admin** — users, analyses, model metrics dashboard.

---

## Local development

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm   # optional
python ml/build_proxy_labels.py && python ml/train.py
uvicorn app.main:app --reload --port 8000
```

Uses SQLite by default (`./arawind.db`). Point at Postgres with:

```bash
export SSG_DATABASE_URL=postgresql+psycopg2://arawind:arawind@localhost:5432/arawind
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Tests

```bash
cd backend
SSG_DATABASE_URL=sqlite:///./test_arawind.db pytest tests/ -q
```

---

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/architecture.md](docs/architecture.md) | System design, data flow, components |
| [docs/deployment.md](docs/deployment.md) | Docker, env vars, security checklist |
| [docs/ml_model.md](docs/ml_model.md) | Features, training, metrics, edge cases |
| [docs/ethics.md](docs/ethics.md) | Bias, privacy, probabilistic disclaimers |
| [docs/testing_plan.md](docs/testing_plan.md) | Test matrix |
| [docs/demo_script.md](docs/demo_script.md) | Live demo walkthrough |
| [docs/evaluation_report.md](docs/evaluation_report.md) | Latest metrics snapshot |
| [docs/api_reference.md](docs/api_reference.md) | Endpoints & examples |

---

## License

Open-source academic demo — free for coursework and learning.
