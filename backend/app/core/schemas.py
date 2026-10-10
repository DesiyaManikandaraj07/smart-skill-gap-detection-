"""Pydantic request/response schemas for the public API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


class SkillImpact(BaseModel):
    skill: str
    impact_pct: float = Field(..., description="Estimated lift in selection % if skill is gained")
    demand_rank: int
    demand_frequency: float = 0.0


class RoadmapItem(BaseModel):
    skill: str
    weeks: int
    projects: list[str] = []
    courses: list[str] = []
    certs: list[str] = []
    rationale: str = ""


class ExplanationItem(BaseModel):
    feature: str
    contribution: float
    direction: str = Field("positive", description="positive | negative")


class CandidateProfile(BaseModel):
    skills: list[str] = []
    education: list[str] = []
    projects: list[str] = []
    internships: list[str] = []
    certifications: list[str] = []
    experience_years: float = 0.0
    cgpa: Optional[float] = None
    locations: list[str] = []
    raw_text_chars: int = 0


class GateResultSchema(BaseModel):
    key: str
    label: str
    passed: bool
    required: str
    observed: str
    severity: str = "hard"
    advice: str = ""


class CoachingSummary(BaseModel):
    headline: str
    verdict: str
    strengths: list[str] = []
    improvements: list[str] = []
    critical_blockers: list[str] = []
    effective_note: str = ""
    gates: list[GateResultSchema] = []
    eligible: bool = True


class AnalyzeResponse(BaseModel):
    id: Optional[int] = None
    candidate_name: str
    role_id: Optional[str] = None
    role_title: Optional[str] = None
    selection_likelihood_pct: float
    effective_selection_pct: float = Field(
        ...,
        description="Capped at ~0 when hard gates fail; otherwise equals skills model %",
    )
    confidence: float
    eligible: bool = True
    matched_skills: list[str]
    missing_skills: list[str]
    weak_skills: list[str]
    required_skills: list[str] = []
    learn_next: list[SkillImpact]
    roadmap: list[RoadmapItem]
    explanations: list[ExplanationItem]
    profile: CandidateProfile
    job_skills: list[str] = []
    summary: Optional[CoachingSummary] = None
    disclaimer: str = (
        "Selection likelihood is a probabilistic estimate from proxy-trained models — "
        "not a hiring guarantee. Hard gates (CGPA, experience, location, degree) can "
        "override skills scoring, as in real ATS pipelines."
    )


class WhatIfRequest(BaseModel):
    candidate_name: str = "Candidate"
    current_skills: list[str]
    add_skills: list[str] = []
    job_skills: list[str]
    job_description: str = ""
    experience_years: float = 0.0
    project_count: int = 0
    cert_count: int = 0
    has_degree: bool = True
    eligible: bool = True


class WhatIfResponse(BaseModel):
    selection_likelihood_pct: float
    effective_selection_pct: float = 0.0
    previous_pct: Optional[float] = None
    delta_pct: float = 0.0
    matched_skills: list[str]
    missing_skills: list[str]
    explanations: list[ExplanationItem] = []
    note: str = ""


class RoleSummary(BaseModel):
    id: str
    title: str
    category: str
    skill_count: int
    summary: str
    min_experience_years: Optional[float] = None
    min_cgpa: Optional[float] = None


class SampleJD(BaseModel):
    id: str
    title: str
    category: str
    description: str
    required_skills: list[str]
    min_experience_years: Optional[float] = None
    min_cgpa: Optional[float] = None
    degree_required: bool = True
    locations: list[str] = []
    experience_level: Optional[str] = None
    company: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None


class JobFeedItem(BaseModel):
    id: str
    title: str
    company: str
    category: str
    experience_level: str  # entry | mid | senior
    summary: str
    description: str
    required_skills: list[str]
    min_experience_years: Optional[float] = None
    min_cgpa: Optional[float] = None
    degree_required: bool = True
    locations: list[str] = []
    source: str = "curated"
    source_url: str = ""
    posted_at: str = ""
    salary: str = ""


# ---- Auth ----
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_admin: bool
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LoginFormResponse(TokenResponse):
    pass


# ---- Admin ----
class AdminStats(BaseModel):
    users_total: int
    analyses_total: int
    analyses_today: int
    avg_selection_pct: float
    ineligible_rate: float
    model_name: str
    model_metrics: dict[str, Any] = {}


class AnalysisListItem(BaseModel):
    id: int
    user_email: str
    candidate_name: str
    role_title: Optional[str]
    selection_likelihood_pct: float
    effective_selection_pct: float = 0.0
    eligible: bool
    created_at: datetime
