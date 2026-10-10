"""Train a heavy gradient-boosted selection model with gate-aware features."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split

FEATURE_NAMES = [
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

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed" / "training_features.csv"
MODELS = ROOT / "app" / "models"
METRICS_OUT = ROOT / "data" / "processed" / "metrics.json"


def get_model():
    try:
        from xgboost import XGBClassifier

        return (
            XGBClassifier(
                n_estimators=400,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.85,
                colsample_bytree=0.85,
                min_child_weight=2,
                reg_lambda=1.2,
                eval_metric="logloss",
                random_state=42,
                n_jobs=4,
            ),
            "xgboost_heavy",
        )
    except Exception:  # noqa: BLE001
        try:
            return (
                HistGradientBoostingClassifier(
                    max_depth=6,
                    learning_rate=0.06,
                    max_iter=300,
                    l2_regularization=0.1,
                    random_state=42,
                ),
                "hist_gradient_boosting",
            )
        except Exception:  # noqa: BLE001
            return (
                RandomForestClassifier(
                    n_estimators=300,
                    max_depth=12,
                    class_weight="balanced_subsample",
                    random_state=42,
                    n_jobs=4,
                ),
                "random_forest_heavy",
            )


def main():
    if not PROCESSED.exists():
        try:
            from ml.build_proxy_labels import main as build
        except ImportError:
            from build_proxy_labels import main as build

        build()

    df = pd.read_csv(PROCESSED)
    for col in FEATURE_NAMES:
        if col not in df.columns:
            df[col] = 0.0
    X = df[FEATURE_NAMES].astype(float).to_numpy()
    y = df["selected"].astype(int).to_numpy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model, name = get_model()
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_f1 = float(cross_val_score(model, X_train, y_train, cv=cv, scoring="f1").mean())
    cv_acc = float(cross_val_score(model, X_train, y_train, cv=cv, scoring="accuracy").mean())

    model.fit(X_train, y_train)
    proba = np.asarray(model.predict_proba(X_test))[:, 1]
    pred = (proba >= 0.5).astype(int)

    # Probability calibration
    calibrator = LogisticRegression(max_iter=400)
    train_proba = np.asarray(model.predict_proba(X_train))[:, 1].reshape(-1, 1)
    calibrator.fit(train_proba, y_train)
    cal_proba = np.asarray(calibrator.predict_proba(proba.reshape(-1, 1)))[:, 1]
    cal_pred = (cal_proba >= 0.5).astype(int)

    metrics = {
        "model_name": f"{name}_calibrated",
        "cv_f1": round(cv_f1, 4),
        "cv_accuracy": round(cv_acc, 4),
        "test_accuracy": round(float(accuracy_score(y_test, cal_pred)), 4),
        "test_precision": round(float(precision_score(y_test, cal_pred, zero_division=0)), 4),
        "test_recall": round(float(recall_score(y_test, cal_pred, zero_division=0)), 4),
        "test_f1": round(float(f1_score(y_test, cal_pred, zero_division=0)), 4),
        "test_roc_auc": round(float(roc_auc_score(y_test, cal_proba)), 4),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "n_total": len(df),
        "positive_rate": round(float(np.mean(y)), 4),
        "feature_names": FEATURE_NAMES,
        "label_note": "Proxy/synthetic labels with hard-gate edge cases — not real hiring outcomes",
        "calibrated": True,
        "architecture": name,
    }

    MODELS.mkdir(parents=True, exist_ok=True)
    bundle = {
        "model": model,
        "calibrator": calibrator,
        "feature_names": FEATURE_NAMES,
        "model_name": metrics["model_name"],
        "cv_f1": metrics["cv_f1"],
        "metrics": metrics,
    }
    out_path = MODELS / "selection_model.joblib"
    joblib.dump(bundle, out_path)
    METRICS_OUT.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"Saved model -> {out_path}")


if __name__ == "__main__":
    main()
