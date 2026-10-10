# Evaluation report

**Labels:** proxy/synthetic with hard-gate edge cases — **not** real hiring outcomes.

## Latest training run

| Metric | Value |
|--------|-------|
| Architecture | HistGradientBoosting (or XGBoost when available) + sigmoid calibration |
| Rows | 25,000 |
| Positive rate | ~0.45 |
| CV F1 | ~0.87 |
| CV Accuracy | ~0.88 |
| Test Accuracy | ~0.88 |
| Test Precision | ~0.87 |
| Test Recall | ~0.86 |
| Test F1 | ~0.87 |
| Test ROC-AUC | ~0.93 |

Exact values: `backend/data/processed/metrics.json`.

## Edge-case coverage in training

- Perfect and zero skill overlap
- Insufficient experience vs JD minimum
- CGPA below cutoff
- Missing degree when required
- Noisy embedding similarity
- 2% random label flips for robustness

## Product-level evaluation (manual)

1. Strong profile + all gates pass → high skills % and equal effective %.
2. Strong skills + failed CGPA gate → skills % may be mid/high, **effective = 0**, critical blockers listed.
3. What-if with failed gates → skills delta moves; effective stays 0; note explains why.
