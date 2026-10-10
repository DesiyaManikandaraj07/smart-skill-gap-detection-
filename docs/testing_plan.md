# Testing plan

## Automated (`pytest`)

| Test | Intent |
|------|--------|
| `test_health` | Service up |
| `test_register_login_me` | Auth round-trip |
| `test_list_roles` | Catalog loads |
| `test_analyze_resume` | Full pipeline + summary |
| `test_hard_gate_cgpa_blocks_effective_score` | Effective % = 0 on CGPA fail |
| `test_what_if` | Skill addition lifts score |

```bash
cd backend
SSG_DATABASE_URL=sqlite:///./test_arawind.db pytest tests/ -q
```

## Manual UI

1. Register → analyze → results persist (admin sees row).
2. Guest analyze → works without token.
3. Hard-gate fail → red banner + blockers.
4. What-if toggles animate score; note when ineligible.
5. Admin disable user → login blocked.
6. Mobile width stacks panels cleanly.
7. Fonts: Fraunces headings, IBM Plex body, mono metrics.

## Docker smoke

```bash
docker compose up --build
curl -s http://localhost:8000/health
open http://localhost:3000
```
