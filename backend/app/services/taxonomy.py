"""ESCO/O*NET hybrid skill catalog + alias normalization."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from app.core.config import settings


@lru_cache(maxsize=1)
def _load_aliases() -> dict[str, str]:
    path = settings.taxonomy_dir / "aliases.json"
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)
    return {k.lower().strip(): v for k, v in raw.items()}


@lru_cache(maxsize=1)
def _load_catalog() -> dict:
    path = settings.taxonomy_dir / "skills_catalog.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def skill_set() -> set[str]:
    catalog = _load_catalog()
    skills = {s for s in catalog.get("skills", [])}
    # Include canonical alias targets
    skills.update(_load_aliases().values())
    return skills


def normalize_skill(raw: str) -> str | None:
    """Map a raw skill string to a canonical taxonomy skill, if known."""
    if not raw:
        return None
    text = raw.strip()
    if not text:
        return None
    aliases = _load_aliases()
    key = re.sub(r"\s+", " ", text.lower())
    if key in aliases:
        return aliases[key]
    # Exact case-insensitive match against catalog
    for skill in skill_set():
        if skill.lower() == key:
            return skill
    return None


def normalize_many(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        canon = normalize_skill(item)
        if canon and canon not in seen:
            seen.add(canon)
            out.append(canon)
    return out


def parse_skill_text(blob: str) -> list[str]:
    """Split a free-text skills field (comma/semicolon/newline) and normalize."""
    if not blob:
        return []
    parts = re.split(r"[,;\n|/]+", blob)
    return normalize_many(p.strip() for p in parts if p.strip())


def catalog_skills_sorted() -> list[str]:
    return sorted(skill_set(), key=str.lower)


def roadmap_resources_path() -> Path:
    return settings.taxonomy_dir / "roadmap_resources.json"
