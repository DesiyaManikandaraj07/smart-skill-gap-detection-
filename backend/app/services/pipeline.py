"""End-to-end analyze pipeline with hard gates, coaching summary, and persistence hooks."""

from __future__ import annotations

import re

from app.core.schemas import (
    AnalyzeResponse,
    CandidateProfile,
    WhatIfRequest,
    WhatIfResponse,
)
from app.services.explainability import explain_score
from app.services.gap_ranker import rank_missing_skills
from app.services.hard_gates import evaluate_gates
from app.services.matcher import extract_job_skills, match_profile
from app.services.pdf_parser import extract_text_from_pdf
from app.services.roadmap import build_roadmap
from app.services.roles_loader import get_role, role_meta
from app.services.scorer import build_feature_vector, score_selection
from app.services.skill_extractor import extract_structured_resume
from app.services.summary import build_coaching_summary
from app.services.taxonomy import normalize_many


def _has_degree(education: list[str], text: str) -> bool:
    blob = " ".join(education) + " " + text
    return bool(
        re.search(
            r"\b(b\.?tech|b\.?e\.?|b\.?sc|bachelor|master|m\.?tech|m\.?s\.?|mba|ph\.?d|degree)\b",
            blob,
            re.I,
        )
    )


def analyze_resume(
    *,
    pdf_bytes: bytes,
    candidate_name: str,
    extra_skills: str = "",
    role_id: str | None = None,
    job_description: str = "",
    candidate_location: str = "",
    candidate_cgpa: float | None = None,
) -> AnalyzeResponse:
    text = extract_text_from_pdf(pdf_bytes)
    resume = extract_structured_resume(text, extra_skills=extra_skills)

    role = get_role(role_id) if role_id else None
    jd_text = job_description.strip()
    seed_skills: list[str] = []
    role_title = None
    meta = role_meta(role_id)

    if role:
        role_title = role.title
        seed_skills = list(role.required_skills)
        if not jd_text:
            jd_text = role.description
        meta = {
            "min_experience_years": role.min_experience_years,
            "min_cgpa": role.min_cgpa,
            "degree_required": role.degree_required,
            "locations": list(role.locations),
        }

    if not jd_text and not seed_skills:
        raise ValueError("Provide a role_id or a job_description.")

    job_skills = extract_job_skills(jd_text, seed_skills=seed_skills)
    if not job_skills and seed_skills:
        job_skills = normalize_many(seed_skills)

    match = match_profile(resume.skills, resume.raw_text, job_skills, jd_text)
    has_degree = _has_degree(resume.education, resume.raw_text)
    cgpa = candidate_cgpa if candidate_cgpa is not None else resume.cgpa

    eligibility = evaluate_gates(
        resume_text=resume.raw_text,
        experience_years=resume.experience_years,
        has_degree=has_degree,
        education_lines=resume.education,
        job_description=jd_text,
        role_meta=meta,
        candidate_location=candidate_location or " ".join(resume.locations),
        candidate_cgpa=cgpa,
    )
    meets_exp = 0.0 if any(g.key == "experience" and not g.passed for g in eligibility.hard_failures) else 1.0

    features = build_feature_vector(
        skill_overlap=match.overlap_ratio,
        jaccard=match.jaccard,
        embedding_similarity=match.embedding_similarity,
        experience_years=resume.experience_years,
        project_count=len(resume.projects),
        cert_count=len(resume.certifications),
        skill_count=len(resume.skills),
        job_skill_count=len(match.job_skills),
        has_degree=has_degree,
        missing_count=len(match.missing),
        cgpa_norm=float(cgpa) / 4.0 if cgpa is not None else 0.5,
        meets_exp_gate=meets_exp,
        gate_fail_count=float(eligibility.failure_count),
    )

    scored = score_selection(features)
    skills_pct = round(scored.probability * 100.0, 1)
    # Real-world: hard gate failure → effective outlook near zero
    effective_pct = 0.0 if not eligibility.eligible else skills_pct

    learn_next = rank_missing_skills(
        missing=match.missing,
        current_skills=resume.skills,
        job_skills=match.job_skills,
        base_features={k: features[k] for k in features if k in {
            "skill_overlap", "jaccard", "embedding_similarity", "experience_years",
            "project_count", "cert_count", "skill_count", "job_skill_count",
            "has_degree", "missing_count",
        }},
        experience_years=resume.experience_years,
        project_count=len(resume.projects),
        cert_count=len(resume.certifications),
        has_degree=has_degree,
        embedding_similarity=match.embedding_similarity,
        role_id=role_id,
    )
    roadmap = build_roadmap(learn_next)
    explanations = explain_score({k: v for k, v in features.items() if k in {
        "skill_overlap", "jaccard", "embedding_similarity", "experience_years",
        "project_count", "cert_count", "skill_count", "job_skill_count",
        "has_degree", "missing_count",
    }})

    summary = build_coaching_summary(
        candidate_name=candidate_name.strip() or "Candidate",
        role_title=role_title,
        matched=match.matched,
        missing=match.missing,
        weak=match.weak,
        experience_years=resume.experience_years,
        project_count=len(resume.projects),
        cert_count=len(resume.certifications),
        has_degree=has_degree,
        selection_pct=skills_pct,
        eligibility=eligibility,
        learn_next_skills=[x.skill for x in learn_next],
    )

    return AnalyzeResponse(
        candidate_name=candidate_name.strip() or "Candidate",
        role_id=role_id,
        role_title=role_title,
        selection_likelihood_pct=skills_pct,
        effective_selection_pct=effective_pct,
        confidence=round(scored.confidence, 3),
        eligible=eligibility.eligible,
        matched_skills=match.matched,
        missing_skills=match.missing,
        weak_skills=match.weak,
        required_skills=match.job_skills,
        learn_next=learn_next,
        roadmap=roadmap,
        explanations=explanations,
        profile=CandidateProfile(
            skills=resume.skills,
            education=resume.education,
            projects=resume.projects,
            internships=resume.internships,
            certifications=resume.certifications,
            experience_years=resume.experience_years,
            cgpa=cgpa,
            locations=resume.locations,
            raw_text_chars=len(resume.raw_text),
        ),
        job_skills=match.job_skills,
        summary=summary,
    )


def run_what_if(req: WhatIfRequest) -> WhatIfResponse:
    from app.services.matcher import embedding_similarity
    from app.services.scorer import predict_with_added_skills

    current = normalize_many(req.current_skills)
    job = normalize_many(req.job_skills)
    emb = embedding_similarity(
        ", ".join(current),
        ", ".join(job) or req.job_description,
    )

    base = predict_with_added_skills(
        base_features={},
        current_skills=current,
        add_skills=[],
        job_skills=job,
        experience_years=req.experience_years,
        project_count=req.project_count,
        cert_count=req.cert_count,
        has_degree=req.has_degree,
        embedding_similarity=emb,
    )
    updated = predict_with_added_skills(
        base_features={},
        current_skills=current,
        add_skills=req.add_skills,
        job_skills=job,
        experience_years=req.experience_years,
        project_count=req.project_count,
        cert_count=req.cert_count,
        has_degree=req.has_degree,
        embedding_similarity=emb,
    )
    skills_after = set(normalize_many(current + req.add_skills))
    matched = sorted(skills_after & set(job))
    missing = sorted(set(job) - skills_after)
    prev = base.probability * 100.0
    new = updated.probability * 100.0
    effective = 0.0 if not req.eligible else new
    note = (
        "Hard gates still fail — adding skills will not raise effective outlook until objective requirements clear."
        if not req.eligible
        else "Skills simulation only; hard gates unchanged."
    )
    return WhatIfResponse(
        selection_likelihood_pct=round(new, 1),
        effective_selection_pct=round(effective, 1),
        previous_pct=round(prev, 1),
        delta_pct=round(new - prev, 1),
        matched_skills=matched,
        missing_skills=missing,
        explanations=explain_score(updated.features),
        note=note,
    )
