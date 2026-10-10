# Machine learning model

## Problem framing

Predict `P(selected)` for a candidate–role pair using ATS-style features. Labels are **proxy/synthetic** (no real hire outcomes available). The model is calibrated and gate-aware.

## Features (13)

| Feature | Meaning |
|---------|---------|
| `skill_overlap` | Fraction of JD skills present on resume |
| `jaccard` | Jaccard similarity of skill sets |
| `embedding_similarity` | TF-IDF cosine (or MiniLM if enabled) |
| `experience_years` | Heuristic years from resume |
| `project_count` | Parsed projects |
| `cert_count` | Parsed certifications |
| `skill_count` | Resume skill cardinality |
| `job_skill_count` | JD skill cardinality |
| `has_degree` | Degree keyword signal |
| `missing_count` | Unmatched JD skills |
| `cgpa_norm` | CGPA / 4.0 |
| `meets_exp_gate` | 1 if experience ≥ JD minimum |
| `gate_fail_count` | Count of failed hard gates |

## Architecture

Training prefers, in order:

1. **XGBoost** (`n_estimators=400`, `max_depth=6`) — when OpenMP runtime allows
2. **HistGradientBoostingClassifier** (`max_iter=300`) — strong sklearn fallback
3. **RandomForest** — last resort

A logistic **probability calibrator** is fit on training scores.

At inference, if `gate_fail_count ≥ 1`, probability is also capped (≤ 0.08) and the API sets `effective_selection_pct = 0`.

## Training corpus

`ml/build_proxy_labels.py` generates **25,000** rows covering modes:

- typical / strong / weak / zero / perfect matches
- `gate_fail_cgpa`, `gate_fail_exp`, `gate_fail_degree`
- noisy embeddings + 2% label flip

Optional merge from Kaggle ATS CSV under `data/raw/` via `ml/prepare_data.py`.

## Evaluation protocol

- Stratified 80/20 holdout
- 5-fold stratified CV on train
- Metrics: Accuracy, Precision, Recall, F1, ROC-AUC

Latest numbers live in `backend/data/processed/metrics.json` and `docs/evaluation_report.md`.

## Retrain

```bash
cd backend
python ml/build_proxy_labels.py
python ml/train.py
python ml/evaluate.py
```

## Limitations

Proxy accuracy can be high while real-world hiring accuracy remains unknown. Always surface the product disclaimer and hard-gate narrative.
