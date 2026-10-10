"""Generate large-scale proxy-labeled training rows with edge cases.

Includes:
- Balanced skill-overlap distributions
- Hard-gate failure cases (low CGPA, insufficient experience, missing degree, location mismatch)
- Extreme profiles (zero skills, perfect match, overqualified)
- Noisy embeddings and label flip noise for robustness
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DATA_PROCESSED = ROOT / "data" / "processed"
DATA_RAW = ROOT / "data" / "raw"
SAMPLE_ROLES = ROOT / "data" / "sample_jds" / "roles.json"
CATALOG = ROOT / "data" / "taxonomy" / "skills_catalog.json"

RNG = np.random.default_rng(42)


def load_skills() -> list[str]:
    with CATALOG.open(encoding="utf-8") as f:
        return list(json.load(f)["skills"])


def load_roles() -> list[dict]:
    with SAMPLE_ROLES.open(encoding="utf-8") as f:
        return json.load(f)


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


def _row(
    *,
    overlap,
    jaccard,
    emb,
    experience,
    projects,
    certs,
    skill_count,
    job_skill_count,
    has_degree,
    missing,
    cgpa_norm,
    meets_exp_gate,
    gate_fail_count,
    role_id,
    source,
    force_selected=None,
):
    logit = (
        -2.4
        + 3.1 * overlap
        + 1.15 * jaccard
        + 1.45 * emb
        + 0.12 * min(experience, 8) / 4
        + 0.09 * min(projects, 8) / 4
        + 0.1 * min(certs, 4) / 2
        + 0.28 * has_degree
        - 0.11 * missing / max(job_skill_count, 1)
        + 0.35 * cgpa_norm
        + 0.4 * meets_exp_gate
        - 0.85 * min(gate_fail_count, 3)
        + float(RNG.normal(0, 0.5))
    )
    prob = 1 / (1 + np.exp(-logit))
    # Hard gates dominate: if any gate fails, selection collapses
    if gate_fail_count >= 1:
        prob *= 0.08
    if force_selected is not None:
        selected = int(force_selected)
    else:
        selected = int(RNG.random() < prob)
    # Label noise
    if RNG.random() < 0.02:
        selected = 1 - selected
    return {
        "skill_overlap": float(overlap),
        "jaccard": float(jaccard),
        "embedding_similarity": float(emb),
        "experience_years": float(experience),
        "project_count": int(projects),
        "cert_count": int(certs),
        "skill_count": int(skill_count),
        "job_skill_count": int(job_skill_count),
        "has_degree": int(has_degree),
        "missing_count": int(missing),
        "cgpa_norm": float(cgpa_norm),
        "meets_exp_gate": float(meets_exp_gate),
        "gate_fail_count": float(gate_fail_count),
        "selected": selected,
        "selection_prob_proxy": float(prob),
        "role_id": role_id,
        "source": source,
    }


def synthetic_rows(n: int = 25000) -> pd.DataFrame:
    skills = load_skills()
    roles = load_roles()
    rows = []

    for i in range(n):
        role = roles[i % len(roles)]
        job_skills = list(role["required_skills"])
        min_exp = float(role.get("min_experience_years") or 0)
        min_cgpa = role.get("min_cgpa")
        degree_req = bool(role.get("degree_required", True))

        mode = RNG.choice(
            ["typical", "strong", "weak", "zero", "perfect", "gate_fail_cgpa", "gate_fail_exp", "gate_fail_degree", "noisy"],
            p=[0.35, 0.12, 0.15, 0.05, 0.08, 0.08, 0.07, 0.05, 0.05],
        )

        if mode == "perfect":
            keep_prob = 0.98
        elif mode == "strong":
            keep_prob = RNG.uniform(0.75, 0.95)
        elif mode == "weak":
            keep_prob = RNG.uniform(0.1, 0.35)
        elif mode == "zero":
            keep_prob = 0.0
        else:
            keep_prob = RNG.uniform(0.25, 0.9)

        matched = [s for s in job_skills if RNG.random() < keep_prob]
        extras = RNG.choice(skills, size=int(RNG.integers(0, 10)), replace=False).tolist()
        cand_skills = list(set(matched + extras))
        job_set = set(job_skills)
        cand_set = set(cand_skills)
        overlap = len(cand_set & job_set) / len(job_set) if job_set else 0.0
        union = len(cand_set | job_set)
        jaccard = len(cand_set & job_set) / union if union else 0.0
        missing = len(job_set - cand_set)

        if mode == "gate_fail_exp":
            experience = float(max(0, min_exp - RNG.uniform(0.5, 2.5)))
        elif mode in {"strong", "perfect"}:
            experience = float(min_exp + RNG.uniform(0.5, 5))
        else:
            experience = float(RNG.uniform(0, 8))

        projects = int(RNG.integers(0, 12))
        certs = int(RNG.integers(0, 6))
        has_degree = 0 if mode == "gate_fail_degree" and degree_req else int(RNG.random() > (0.05 if mode != "weak" else 0.35))
        if mode == "gate_fail_cgpa" and min_cgpa:
            cgpa = float(min_cgpa - RNG.uniform(0.2, 1.0))
            cgpa = max(1.5, cgpa)
        elif min_cgpa:
            cgpa = float(RNG.uniform(max(min_cgpa - 0.3, 2.0), 4.0))
        else:
            cgpa = float(RNG.uniform(2.2, 4.0))
        cgpa_norm = cgpa / 4.0

        emb = float(np.clip(overlap * 0.72 + RNG.normal(0.18, 0.09), 0, 1))
        if mode == "noisy":
            emb = float(RNG.uniform(0, 1))

        gate_fails = 0
        meets_exp = 1.0
        if experience + 1e-6 < min_exp:
            gate_fails += 1
            meets_exp = 0.0
        if min_cgpa is not None and cgpa + 1e-6 < float(min_cgpa):
            gate_fails += 1
        if degree_req and not has_degree:
            gate_fails += 1
        if mode in {"gate_fail_cgpa", "gate_fail_exp", "gate_fail_degree"}:
            gate_fails = max(gate_fails, 1)

        rows.append(
            _row(
                overlap=overlap,
                jaccard=jaccard,
                emb=emb,
                experience=experience,
                projects=projects,
                certs=certs,
                skill_count=len(cand_skills),
                job_skill_count=len(job_skills),
                has_degree=has_degree,
                missing=missing,
                cgpa_norm=cgpa_norm,
                meets_exp_gate=meets_exp,
                gate_fail_count=gate_fails,
                role_id=role["id"],
                source=f"synthetic:{mode}",
            )
        )

    return pd.DataFrame(rows)


def try_load_kaggle_ats() -> pd.DataFrame | None:
    candidates = list(DATA_RAW.glob("**/*.csv"))
    for path in candidates:
        try:
            sample = pd.read_csv(path, nrows=3)
        except Exception:  # noqa: BLE001
            continue
        cols = {c.lower(): c for c in sample.columns}
        if "selected" not in cols and "hiring_decision" not in cols:
            continue
        full = pd.read_csv(path)
        def col(*names):
            for n in names:
                if n in cols:
                    return cols[n]
            return None

        selected_col = col("selected", "hiring_decision", "hired")
        kw = col("keyword_match_percentage", "ats_score", "ats_match")
        mapped = pd.DataFrame()
        mapped["skill_overlap"] = (
            pd.to_numeric(full[kw], errors="coerce").fillna(50) / 100.0 if kw else 0.5
        )
        mapped["jaccard"] = mapped["skill_overlap"] * 0.85
        mapped["embedding_similarity"] = np.clip(mapped["skill_overlap"] * 0.7 + 0.2, 0, 1)
        exp = col("years_of_experience", "experience_years", "experience")
        mapped["experience_years"] = pd.to_numeric(full[exp], errors="coerce").fillna(1) if exp else 1.0
        proj = col("projects_completed", "project_count", "projects")
        mapped["project_count"] = pd.to_numeric(full[proj], errors="coerce").fillna(2) if proj else 2
        mapped["cert_count"] = 1
        mapped["skill_count"] = 8
        mapped["job_skill_count"] = 10
        mapped["has_degree"] = 1
        mapped["missing_count"] = ((1 - mapped["skill_overlap"]) * mapped["job_skill_count"]).round()
        mapped["cgpa_norm"] = 0.75
        mapped["meets_exp_gate"] = 1.0
        mapped["gate_fail_count"] = 0.0
        sel = full[selected_col]
        if sel.dtype == object:
            mapped["selected"] = sel.astype(str).str.lower().isin(
                {"selected", "hired", "yes", "1", "true"}
            ).astype(int)
        else:
            mapped["selected"] = pd.to_numeric(sel, errors="coerce").fillna(0).astype(int)
        mapped["selection_prob_proxy"] = mapped["skill_overlap"]
        mapped["role_id"] = "kaggle"
        mapped["source"] = f"kaggle:{path.name}"
        print(f"Loaded Kaggle proxy rows from {path} ({len(mapped)})")
        return mapped
    return None


def build_role_demand(roles: list[dict], skills: list[str]) -> dict:
    global_counts: dict[str, int] = {s: 0 for s in skills}
    per_role: dict[str, dict[str, float]] = {}
    for role in roles:
        req = role["required_skills"]
        freq = {s: (1.0 if s in req else 0.05) for s in skills}
        for s in req:
            freq[s] = 0.55 + 0.4 * (req.index(s) / max(len(req), 1))
            global_counts[s] = global_counts.get(s, 0) + 1
        per_role[role["id"]] = {k: round(v, 4) for k, v in freq.items() if v >= 0.1}
    total = max(sum(global_counts.values()), 1)
    per_role["_global"] = {
        s: round(global_counts.get(s, 0) / total + 0.02, 4) for s in skills if global_counts.get(s, 0)
    }
    return per_role


def main():
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    frames = [synthetic_rows(25000)]
    kaggle = try_load_kaggle_ats()
    if kaggle is not None:
        frames.append(kaggle)
    df = pd.concat(frames, ignore_index=True)
    out = DATA_PROCESSED / "training_features.csv"
    df.to_csv(out, index=False)
    print(f"Wrote {len(df)} rows → {out}  positives={df['selected'].mean():.3f}")

    demand = build_role_demand(load_roles(), load_skills())
    demand_path = DATA_PROCESSED / "role_skill_demand.json"
    with demand_path.open("w", encoding="utf-8") as f:
        json.dump(demand, f, indent=2)
    print(f"Wrote demand table → {demand_path}")


if __name__ == "__main__":
    main()
