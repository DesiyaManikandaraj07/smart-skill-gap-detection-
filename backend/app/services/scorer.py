"""Selection-likelihood scoring with trained model + heuristic fallback."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from app.core.config import settings

DEFAULT_FEATURES = [
    "skill_overlap",
    "jaccard",
    "embedding_similarity",
    "experience_years",
    "project_count",
    "cert_count",
    "skill_count",
    "job_skill_count",
    "has_degree",
    "missing_count",
    "cgpa_norm",
    "meets_exp_gate",
    "gate_fail_count",
]

# Backward-compatible export
FEATURE_NAMES = DEFAULT_FEATURES

@dataclass
class ScoreResult:
    probability: float
    confidence: float
    features: dict[str, float]
    model_name: str


_BUNDLE: dict[str, Any] | None = None


def _model_path() -> Path:
    return settings.models_dir / "selection_model.joblib"


def load_model_bundle() -> dict[str, Any] | None:
    global _BUNDLE
    if _BUNDLE is not None:
        return _BUNDLE
    path = _model_path()
    if not path.exists():
        return None
    _BUNDLE = joblib.load(path)
    return _BUNDLE


def build_feature_vector(
    *,
    skill_overlap: float,
    jaccard: float,
    embedding_similarity: float,
    experience_years: float,
    project_count: int,
    cert_count: int,
    skill_count: int,
    job_skill_count: int,
    has_degree: bool,
    missing_count: int,
    cgpa_norm: float = 0.5,
    meets_exp_gate: float = 1.0,
    gate_fail_count: float = 0.0,
) -> dict[str, float]:
    return {
        "skill_overlap": float(skill_overlap),
        "jaccard": float(jaccard),
        "embedding_similarity": float(embedding_similarity),
        "experience_years": float(min(experience_years, 20.0)),
        "project_count": float(min(project_count, 20)),
        "cert_count": float(min(cert_count, 15)),
        "skill_count": float(min(skill_count, 50)),
        "job_skill_count": float(min(job_skill_count, 40)),
        "has_degree": 1.0 if has_degree else 0.0,
        "missing_count": float(min(missing_count, 40)),
        "cgpa_norm": float(np.clip(cgpa_norm, 0, 1)),
        "meets_exp_gate": float(meets_exp_gate),
        "gate_fail_count": float(gate_fail_count),
    }


def _heuristic_probability(features: dict[str, float]) -> float:
    if features.get("gate_fail_count", 0) >= 1:
        return 0.04
    score = (
        0.32 * features["skill_overlap"]
        + 0.14 * features["jaccard"]
        + 0.18 * features["embedding_similarity"]
        + 0.07 * min(features["experience_years"] / 5.0, 1.0)
        + 0.05 * min(features["project_count"] / 5.0, 1.0)
        + 0.04 * min(features["cert_count"] / 3.0, 1.0)
        + 0.04 * features["has_degree"]
        + 0.08 * features.get("cgpa_norm", 0.5)
        + 0.08 * features.get("meets_exp_gate", 1.0)
    )
    gap_pen = min(features["missing_count"] / max(features["job_skill_count"], 1.0), 1.0)
    score = score * (1.0 - 0.25 * gap_pen)
    return float(max(0.03, min(0.97, score)))


def score_selection(features: dict[str, float]) -> ScoreResult:
    bundle = load_model_bundle()
    names = list((bundle or {}).get("feature_names") or DEFAULT_FEATURES)
    # Fill missing keys
    for n in names:
        features.setdefault(n, 0.0)
    x = np.array([[features.get(n, 0.0) for n in names]], dtype=float)

    if bundle is not None:
        model = bundle["model"]
        calibrator = bundle.get("calibrator")
        try:
            if hasattr(model, "predict_proba"):
                proba = float(model.predict_proba(x)[0, 1])
            else:
                proba = float(np.clip(model.predict(x)[0], 0, 1))
            if calibrator is not None and hasattr(calibrator, "predict_proba"):
                proba = float(calibrator.predict_proba([[proba]])[0, 1])
            # Enforce hard-gate collapse at inference too
            if features.get("gate_fail_count", 0) >= 1:
                proba = min(proba, 0.08)
            proba = max(0.0, min(1.0, proba))
            base_conf = bundle.get("cv_f1", 0.7)
            margin = abs(proba - 0.5) * 2
            confidence = float(max(0.45, min(0.95, 0.4 * base_conf + 0.6 * margin)))
            return ScoreResult(
                probability=proba,
                confidence=confidence,
                features=features,
                model_name=bundle.get("model_name", "trained"),
            )
        except Exception:  # noqa: BLE001
            pass

    proba = _heuristic_probability(features)
    margin = abs(proba - 0.5) * 2
    return ScoreResult(
        probability=proba,
        confidence=float(max(0.4, min(0.85, 0.5 + 0.35 * margin))),
        features=features,
        model_name="heuristic_fallback",
    )


def predict_with_added_skills(
    *,
    base_features: dict[str, float],
    current_skills: list[str],
    add_skills: list[str],
    job_skills: list[str],
    experience_years: float,
    project_count: int,
    cert_count: int,
    has_degree: bool,
    embedding_similarity: float,
) -> ScoreResult:
    from app.services.taxonomy import normalize_many

    skills = set(normalize_many(current_skills + add_skills))
    job = set(normalize_many(job_skills))
    matched = skills & job
    missing = job - skills
    overlap = len(matched) / len(job) if job else 0.0
    union = len(skills | job)
    jaccard = len(matched) / union if union else 0.0
    features = build_feature_vector(
        skill_overlap=overlap,
        jaccard=jaccard,
        embedding_similarity=embedding_similarity,
        experience_years=experience_years,
        project_count=project_count,
        cert_count=cert_count,
        skill_count=len(skills),
        job_skill_count=len(job),
        has_degree=has_degree,
        missing_count=len(missing),
        cgpa_norm=float(base_features.get("cgpa_norm", 0.5)) if base_features else 0.5,
        meets_exp_gate=float(base_features.get("meets_exp_gate", 1.0)) if base_features else 1.0,
        gate_fail_count=float(base_features.get("gate_fail_count", 0.0)) if base_features else 0.0,
    )
    return score_selection(features)
