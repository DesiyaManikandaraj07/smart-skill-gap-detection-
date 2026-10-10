"""Rank missing skills by demand frequency × estimated score impact."""

from __future__ import annotations

from app.core.schemas import SkillImpact
from app.services.matcher import demand_frequency
from app.services.scorer import predict_with_added_skills, score_selection


def rank_missing_skills(
    *,
    missing: list[str],
    current_skills: list[str],
    job_skills: list[str],
    base_features: dict[str, float],
    experience_years: float,
    project_count: int,
    cert_count: int,
    has_degree: bool,
    embedding_similarity: float,
    role_id: str | None = None,
    top_k: int = 10,
) -> list[SkillImpact]:
    base = score_selection(base_features).probability * 100.0
    ranked: list[SkillImpact] = []

    for skill in missing:
        res = predict_with_added_skills(
            base_features=base_features,
            current_skills=current_skills,
            add_skills=[skill],
            job_skills=job_skills,
            experience_years=experience_years,
            project_count=project_count,
            cert_count=cert_count,
            has_degree=has_degree,
            embedding_similarity=embedding_similarity,
        )
        impact = res.probability * 100.0 - base
        freq = demand_frequency(skill, role_id)
        # Combined priority score for sorting
        ranked.append(
            SkillImpact(
                skill=skill,
                impact_pct=round(max(0.0, impact), 2),
                demand_rank=0,
                demand_frequency=round(freq, 4),
            )
        )

    ranked.sort(key=lambda x: (x.impact_pct * 0.7 + x.demand_frequency * 30 * 0.3), reverse=True)
    for i, item in enumerate(ranked, start=1):
        item.demand_rank = i
    return ranked[:top_k]
