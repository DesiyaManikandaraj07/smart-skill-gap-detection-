"""Re-evaluate the saved model and print a concise report."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed" / "training_features.csv"
MODEL = ROOT / "app" / "models" / "selection_model.joblib"
REPORT = ROOT / "data" / "processed" / "evaluation_report.txt"

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
]


def main():
    bundle = joblib.load(MODEL)
    model = bundle["model"]
    df = pd.read_csv(PROCESSED)
    X = df[FEATURE_NAMES].astype(float).values
    y = df["selected"].astype(int).values
    pred = model.predict(X)
    report = classification_report(y, pred, digits=4)
    cm = confusion_matrix(y, pred)
    text = (
        f"Model: {bundle.get('model_name')}\n"
        f"CV F1 (from training): {bundle.get('cv_f1')}\n\n"
        f"{report}\nConfusion matrix:\n{cm}\n\n"
        "NOTE: Labels are proxy/synthetic. Metrics do not measure real hiring accuracy.\n"
    )
    REPORT.write_text(text, encoding="utf-8")
    print(text)
    metrics_path = ROOT / "data" / "processed" / "metrics.json"
    if metrics_path.exists():
        print(metrics_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
