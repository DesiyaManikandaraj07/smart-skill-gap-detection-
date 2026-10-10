"""Build a learning roadmap for prioritized skills."""

from __future__ import annotations

import json
from functools import lru_cache

from app.core.schemas import RoadmapItem, SkillImpact
from app.services.taxonomy import roadmap_resources_path


@lru_cache(maxsize=1)
def _resources() -> dict:
    path = roadmap_resources_path()
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def build_roadmap(learn_next: list[SkillImpact], max_items: int = 6) -> list[RoadmapItem]:
    resources = _resources()
    default = resources.get("default", {"weeks": 3, "courses": [], "projects": [], "certs": []})
    items: list[RoadmapItem] = []
    for entry in learn_next[:max_items]:
        meta = resources.get(entry.skill, default)
        items.append(
            RoadmapItem(
                skill=entry.skill,
                weeks=int(meta.get("weeks", 3)),
                projects=list(meta.get("projects", [])),
                courses=list(meta.get("courses", [])),
                certs=list(meta.get("certs", [])),
                rationale=(
                    f"Learning {entry.skill} is estimated to lift selection likelihood "
                    f"by ~{entry.impact_pct:.1f} pts (demand rank #{entry.demand_rank})."
                ),
            )
        )
    return items
