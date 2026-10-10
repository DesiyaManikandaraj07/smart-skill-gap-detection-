# Demo script (~10 minutes)

## Setup

```bash
docker compose up --build
```

Open http://localhost:3000. Have `docs/sample_resume.pdf` ready.

## Flow

1. **Product framing (1 min)**  
   “We score skill fit *and* enforce the hard filters recruiters actually use.”

2. **Auth (1 min)**  
   Register a student account → show that analyses will save.  
   Or sign in as admin: `admin@example.com` / `Admin@Arawind2026`.

3. **Happy path (3 min)**  
   Upload sample resume → role **Frontend Engineer** → location Bangalore → CGPA 3.6 → Run.  
   Walk: skills %, effective %, strengths, required skills chips, learn-next, roadmap, what-if.

4. **Hard gate failure (3 min)**  
   Same strong ML skills resume / role **ML Engineer** with CGPA **2.1**.  
   Show banner, critical blockers, effective % = 0, what-if note that skills cannot override gates.

5. **Admin (1 min)**  
   Admin console → users, analyses table, model F1 / ROC-AUC.

6. **Close (1 min)**  
   Docker-universal, open-source, probabilistic disclaimer.

## Backup curl

See `docs/api_reference.md`.
