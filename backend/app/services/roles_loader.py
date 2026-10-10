"""Load curated sample roles / job descriptions (read-only JSON)."""

from __future__ import annotations

import json
from functools import lru_cache

from app.core.config import settings
from app.core.schemas import RoleSummary, SampleJD


@lru_cache(maxsize=1)
def _roles() -> list[dict]:
    path = settings.sample_jds_dir / "roles.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def role_meta(role_id: str | None) -> dict:
    if not role_id:
        return {}
    for r in _roles():
        if r["id"] == role_id:
            return {
                "min_experience_years": r.get("min_experience_years"),
                "min_cgpa": r.get("min_cgpa"),
                "degree_required": r.get("degree_required", True),
                "locations": list(r.get("locations") or []),
            }
    try:
        from app.services.job_feed import get_job

        job = get_job(role_id)
        if job is not None:
            return {
                "min_experience_years": job.min_experience_years,
                "min_cgpa": job.min_cgpa,
                "degree_required": job.degree_required,
                "locations": list(job.locations),
            }
    except Exception:  # noqa: BLE001
        pass
    return {}


def list_roles() -> list[RoleSummary]:
    return [
        RoleSummary(
            id=r["id"],
            title=r["title"],
            category=r["category"],
            skill_count=len(r.get("required_skills", [])),
            summary=r.get("summary", ""),
            min_experience_years=r.get("min_experience_years"),
            min_cgpa=r.get("min_cgpa"),
        )
        for r in _roles()
    ]


def get_role(role_id: str) -> SampleJD | None:
    for r in _roles():
        if r["id"] == role_id:
            return SampleJD(
                id=r["id"],
                title=r["title"],
                category=r["category"],
                description=r["description"],
                required_skills=list(r.get("required_skills", [])),
                min_experience_years=r.get("min_experience_years"),
                min_cgpa=r.get("min_cgpa"),
                degree_required=bool(r.get("degree_required", True)),
                locations=list(r.get("locations") or []),
            )
    # Also resolve jobs from the market feed (curated + live cache)
    try:
        from app.services.job_feed import get_job, job_as_sample

        job = get_job(role_id)
        if job is not None:
            sample = job_as_sample(job)
            sample.experience_level = job.experience_level
            sample.company = job.company
            sample.source = job.source
            sample.source_url = job.source_url
            return sample
    except Exception:  # noqa: BLE001
        pass
    return None
