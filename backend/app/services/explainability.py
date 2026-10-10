"""SHAP / feature-importance explanations for selection scores."""

from __future__ import annotations

from app.core.schemas import ExplanationItem
from app.services.scorer import FEATURE_NAMES, load_model_bundle


def explain_score(features: dict[str, float], top_k: int = 6) -> list[ExplanationItem]:
    bundle = load_model_bundle()
    values: dict[str, float] = {}

    if bundle is not None:
        model = bundle["model"]
        try:
            import numpy as np
            import shap

            x = np.array([[features[n] for n in FEATURE_NAMES]], dtype=float)
            # TreeExplainer for XGBoost / RF; KernelExplainer fallback is slow — skip
            if hasattr(model, "get_booster") or model.__class__.__name__ in {
                "XGBClassifier",
                "RandomForestClassifier",
                "GradientBoostingClassifier",
            }:
                explainer = shap.TreeExplainer(model)
                sv = explainer.shap_values(x)
                if isinstance(sv, list):
                    sv = sv[1]  # positive class
                row = sv[0]
                for name, val in zip(FEATURE_NAMES, row):
                    values[name] = float(val)
            elif hasattr(model, "feature_importances_"):
                imps = model.feature_importances_
                for name, imp, feat_val in zip(FEATURE_NAMES, imps, [features[n] for n in FEATURE_NAMES]):
                    # Signed by centering around typical mid values
                    center = {"skill_overlap": 0.5, "jaccard": 0.35, "embedding_similarity": 0.5}.get(
                        name, 0.0
                    )
                    values[name] = float(imp) * (feat_val - center)
        except Exception:  # noqa: BLE001
            values = {}

    if not values:
        # Transparent contribution approximation for heuristic / fallback
        weights = {
            "skill_overlap": 0.38,
            "jaccard": 0.18,
            "embedding_similarity": 0.22,
            "experience_years": 0.08,
            "project_count": 0.06,
            "cert_count": 0.04,
            "has_degree": 0.04,
            "missing_count": -0.12,
            "skill_count": 0.02,
            "job_skill_count": 0.0,
        }
        for name, w in weights.items():
            feat = features.get(name, 0.0)
            if name == "experience_years":
                feat = min(feat / 5.0, 1.0)
            elif name == "project_count":
                feat = min(feat / 5.0, 1.0)
            elif name == "cert_count":
                feat = min(feat / 3.0, 1.0)
            elif name == "missing_count":
                feat = min(feat / max(features.get("job_skill_count", 1.0), 1.0), 1.0)
            values[name] = w * feat

    items = [
        ExplanationItem(
            feature=name,
            contribution=round(val, 4),
            direction="positive" if val >= 0 else "negative",
        )
        for name, val in values.items()
    ]
    items.sort(key=lambda x: abs(x.contribution), reverse=True)
    return items[:top_k]
