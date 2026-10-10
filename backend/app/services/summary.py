"""Narrative coaching summary — strengths, gaps, and next actions."""

from __future__ import annotations

from app.core.schemas import CoachingSummary, GateResultSchema
from app.services.hard_gates import EligibilityReport


def build_coaching_summary(
    *,
    candidate_name: str,
    role_title: str | None,
    matched: list[str],
    missing: list[str],
    weak: list[str],
    experience_years: float,
    project_count: int,
    cert_count: int,
    has_degree: bool,
    selection_pct: float,
    eligibility: EligibilityReport,
    learn_next_skills: list[str],
) -> CoachingSummary:
    role = role_title or "the target role"
    strengths: list[str] = []
    improvements: list[str] = []
    critical: list[str] = []

    if matched:
        strengths.append(
            f"You already cover {len(matched)} required skill(s) for {role}: "
            + ", ".join(matched[:8])
            + ("…" if len(matched) > 8 else "")
            + "."
        )
    if project_count >= 2:
        strengths.append(
            f"You list {project_count} projects — concrete proof of applied skill helps more than keyword lists alone."
        )
    elif project_count == 1:
        strengths.append("You have at least one project on the resume; expand outcomes and tech stack detail.")
    if cert_count >= 1:
        strengths.append(
            f"{cert_count} certification signal(s) found — useful for roles that screen on formal credentials."
        )
    if experience_years >= 1:
        strengths.append(
            f"Detected ~{experience_years:g} year(s) of experience, which supports mid-funnel credibility."
        )
    if has_degree:
        strengths.append("Education section shows a degree signal that clears common degree hard-filters.")
    if selection_pct >= 70 and eligibility.eligible:
        strengths.append(
            f"At {selection_pct:.0f}% selection likelihood (skills model), your profile is competitive on paper for {role}."
        )

    if not strengths:
        strengths.append(
            "Your resume was readable, but few role-aligned strengths stood out yet — focus the rewrite on proof."
        )

    if missing:
        improvements.append(
            f"Priority skill gaps vs {role}: " + ", ".join(missing[:10]) + "."
        )
    if weak:
        improvements.append(
            "These skills appear lightly evidenced (mention once / no depth): "
            + ", ".join(weak[:8])
            + ". Add bullets with tools, metrics, or ownership."
        )
    if project_count < 2:
        improvements.append(
            "Add 1–2 portfolio projects that exercise the missing stack — recruiters weight demonstrated work heavily for students."
        )
    if experience_years < 1:
        improvements.append(
            "Experience signal is thin. Internships, research, open-source, or freelance gigs help even if short."
        )
    if learn_next_skills:
        improvements.append(
            "Highest-impact skills to learn next (model estimate): "
            + ", ".join(learn_next_skills[:5])
            + "."
        )

    for g in eligibility.hard_failures:
        critical.append(f"[Hard gate] {g.label}: required {g.required}; observed {g.observed}. {g.advice}")

    if not eligibility.eligible:
        headline = (
            f"{candidate_name}, skill fit alone is not enough for {role} right now — "
            f"{len(eligibility.hard_failures)} objective requirement(s) fail typical ATS hard filters."
        )
        verdict = "ineligible_hard_gates"
    elif selection_pct >= 70:
        headline = (
            f"{candidate_name}, you look well-aligned for {role}. Tighten weak evidence and close the remaining gaps."
        )
        verdict = "competitive"
    elif selection_pct >= 45:
        headline = (
            f"{candidate_name}, you are borderline for {role}. A focused skill sprint plus clearer proof can move the needle."
        )
        verdict = "borderline"
    else:
        headline = (
            f"{candidate_name}, the gap to {role} is significant. Prioritize the top missing skills and rebuild project proof."
        )
        verdict = "early"

    # Effective score note
    if not eligibility.eligible:
        effective_note = (
            "Effective selection outlook is capped near zero until hard gates clear — "
            "recruiters often never see the skills score."
        )
    else:
        effective_note = (
            f"Skills-based selection likelihood: {selection_pct:.1f}%. "
            "Treat this as a probabilistic screening estimate, not an offer prediction."
        )

    return CoachingSummary(
        headline=headline,
        verdict=verdict,
        strengths=strengths,
        improvements=improvements,
        critical_blockers=critical,
        effective_note=effective_note,
        gates=[
            GateResultSchema(
                key=g.key,
                label=g.label,
                passed=g.passed,
                required=g.required,
                observed=g.observed,
                severity=g.severity,
                advice=g.advice,
            )
            for g in eligibility.gates
        ],
        eligible=eligibility.eligible,
    )
