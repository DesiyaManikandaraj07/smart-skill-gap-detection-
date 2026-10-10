"""Lexical + semantic matching between resume skills and job requirements."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from app.core.config import settings
from app.services.taxonomy import normalize_many, normalize_skill, skill_set


@dataclass
class MatchResult:
    job_skills: list[str]
    matched: list[str]
    missing: list[str]
    weak: list[str]
    overlap_ratio: float
    jaccard: float
    embedding_similarity: float


_EMBEDDER = None
_EMBEDDER_FAILED = False
_TFIDF = None


def _get_embedder():
    global _EMBEDDER, _EMBEDDER_FAILED
    if _EMBEDDER_FAILED or not settings.use_sentence_transformers:
        return None
    if _EMBEDDER is not None:
        return _EMBEDDER
    try:
        from sentence_transformers import SentenceTransformer

        _EMBEDDER = SentenceTransformer(settings.embedding_model)
        return _EMBEDDER
    except Exception:  # noqa: BLE001
        _EMBEDDER_FAILED = True
        return None


def _tfidf_similarity(a: str, b: str) -> float:
    global _TFIDF
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    if _TFIDF is None:
        _TFIDF = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    try:
        matrix = _TFIDF.fit_transform([a or " ", b or " "])
        sim = float(cosine_similarity(matrix[0:1], matrix[1:2])[0, 0])
        return max(0.0, min(1.0, sim))
    except Exception:  # noqa: BLE001
        return 0.0


def embedding_similarity(text_a: str, text_b: str) -> float:
    embedder = _get_embedder()
    if embedder is None:
        return _tfidf_similarity(text_a, text_b)
    try:
        vectors = embedder.encode([text_a[:4000], text_b[:4000]], normalize_embeddings=True)
        sim = float(np.dot(vectors[0], vectors[1]))
        return max(0.0, min(1.0, (sim + 1) / 2)) if sim < 0 else max(0.0, min(1.0, sim))
    except Exception:  # noqa: BLE001
        return _tfidf_similarity(text_a, text_b)


def extract_job_skills(job_description: str, seed_skills: list[str] | None = None) -> list[str]:
    """Pull required skills from a JD using catalog matching + optional seeds."""
    found: list[str] = []
    if seed_skills:
        found.extend(seed_skills)
    if job_description:
        lower = job_description.lower()
        for skill in sorted(skill_set(), key=len, reverse=True):
            pat = re.compile(rf"(?<![a-z0-9]){re.escape(skill.lower())}(?![a-z0-9])")
            if pat.search(lower):
                found.append(skill)
    return normalize_many(found)


def classify_skill_strength(skill: str, resume_text: str) -> str:
    """Heuristic: mentioned once → weak; multiple / in skills section context → strong."""
    pattern = re.compile(rf"(?<![a-z0-9]){re.escape(skill)}(?![a-z0-9])", re.I)
    hits = pattern.findall(resume_text)
    if len(hits) <= 1:
        # Also check years/expertise phrases
        expert = re.search(
            rf"(?:proficient|expert|advanced|years?).{{0,20}}{re.escape(skill)}",
            resume_text,
            re.I,
        )
        if expert:
            return "strong"
        return "weak"
    return "strong"


def match_profile(
    resume_skills: list[str],
    resume_text: str,
    job_skills: list[str],
    job_description: str = "",
) -> MatchResult:
    resume_set = set(normalize_many(resume_skills))
    job_list = normalize_many(job_skills)
    job_set = set(job_list)

    matched = sorted(resume_set & job_set)
    missing = sorted(job_set - resume_set)

    weak = []
    strong_matched = []
    for skill in matched:
        strength = classify_skill_strength(skill, resume_text)
        if strength == "weak":
            weak.append(skill)
        else:
            strong_matched.append(skill)

    overlap = len(matched) / len(job_set) if job_set else 0.0
    union = len(resume_set | job_set)
    jaccard = len(resume_set & job_set) / union if union else 0.0

    resume_blob = ", ".join(sorted(resume_set)) or resume_text[:1500]
    job_blob = ", ".join(job_list) or job_description[:1500]
    emb = embedding_similarity(resume_blob, job_blob)

    return MatchResult(
        job_skills=job_list,
        matched=matched,
        missing=missing,
        weak=weak,
        overlap_ratio=overlap,
        jaccard=jaccard,
        embedding_similarity=emb,
    )


@lru_cache(maxsize=1)
def role_demand_frequencies() -> dict[str, dict[str, float]]:
    """Load precomputed skill demand frequencies per role (from processed corpus)."""
    import json
    from pathlib import Path

    path = Path(settings.processed_dir) / "role_skill_demand.json"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def demand_frequency(skill: str, role_id: str | None = None) -> float:
    data = role_demand_frequencies()
    if role_id and role_id in data:
        return float(data[role_id].get(skill, data.get("_global", {}).get(skill, 0.05)))
    return float(data.get("_global", {}).get(skill, 0.05))
