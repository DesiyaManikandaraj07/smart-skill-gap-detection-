"""Objective eligibility gates — fail closed regardless of skill score.

Mirrors real ATS / recruiter hard filters: CGPA, years of experience,
work authorization / location, degree level, and age of graduation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class GateResult:
    key: str
    label: str
    passed: bool
    required: str
    observed: str
    severity: str = "hard"  # hard | soft
    advice: str = ""


@dataclass
class EligibilityReport:
    eligible: bool
    gates: list[GateResult] = field(default_factory=list)
    hard_failures: list[GateResult] = field(default_factory=list)
    soft_warnings: list[GateResult] = field(default_factory=list)

    @property
    def failure_count(self) -> int:
        return len(self.hard_failures)


def extract_cgpa(text: str) -> float | None:
    patterns = [
        re.compile(r"\bcgpa\s*[:=]?\s*(\d(?:\.\d{1,2})?)\s*(?:/\s*([48]|10))?", re.I),
        re.compile(r"\bgpa\s*[:=]?\s*(\d(?:\.\d{1,2})?)\s*(?:/\s*([48]|10))?", re.I),
        re.compile(r"\b(?:cgpa|gpa)\s+of\s+(\d(?:\.\d{1,2})?)", re.I),
    ]
    for pat in patterns:
        m = pat.search(text)
        if not m:
            continue
        val = float(m.group(1))
        scale = float(m.group(2)) if m.lastindex and m.group(2) else None
        if scale == 10 or (scale is None and val > 4.5):
            # Normalize 10-point to 4-point approx
            return round(val / 10.0 * 4.0, 2) if val <= 10 else None
        if val <= 4.0:
            return val
        if val <= 10:
            return round(val / 10.0 * 4.0, 2)
    return None


def extract_locations(text: str) -> list[str]:
    # Simple city / country / remote cues
    known = [
        "remote",
        "hybrid",
        "onsite",
        "bangalore",
        "bengaluru",
        "hyderabad",
        "chennai",
        "mumbai",
        "pune",
        "delhi",
        "noida",
        "gurgaon",
        "gurugram",
        "kolkata",
        "san francisco",
        "new york",
        "seattle",
        "austin",
        "london",
        "toronto",
        "berlin",
        "singapore",
        "india",
        "united states",
        "usa",
        "uk",
        "canada",
        "germany",
    ]
    lower = text.lower()
    found = [k for k in known if re.search(rf"\b{re.escape(k)}\b", lower)]
    return found


def parse_jd_requirements(job_description: str, role_meta: dict | None = None) -> dict:
    """Pull hard requirements from JD text and optional role metadata."""
    meta = role_meta or {}
    jd = job_description or ""
    lower = jd.lower()

    min_exp = meta.get("min_experience_years")
    m = re.search(r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:relevant\s+)?experience", lower)
    if m:
        min_exp = float(m.group(1))
    if min_exp is None:
        m2 = re.search(r"minimum\s+(\d+)\s+years?", lower)
        if m2:
            min_exp = float(m2.group(1))

    min_cgpa = meta.get("min_cgpa")
    m = re.search(r"(?:minimum|min\.?|at least)\s+(?:cgpa|gpa)\s*(?:of\s*)?(\d(?:\.\d)?)", lower)
    if m:
        min_cgpa = float(m.group(1))
        if min_cgpa > 4.5:
            min_cgpa = round(min_cgpa / 10 * 4, 2)

    degree_required = meta.get("degree_required", True)
    if re.search(r"bachelor'?s|b\.?tech|b\.?e\.?|degree\s+required|must\s+have\s+a\s+degree", lower):
        degree_required = True
    if re.search(r"no\s+degree\s+required|degree\s+optional", lower):
        degree_required = False

    locations: list[str] = list(meta.get("locations") or [])
    for loc in extract_locations(jd):
        if loc not in locations:
            locations.append(loc)
    # Prefer explicit "must be based in X"
    m = re.search(r"(?:must be|based in|location[:\s]+|work from)\s*([A-Za-z .,]{3,40})", jd, re.I)
    if m:
        locations.insert(0, m.group(1).strip().lower())

    work_auth = None
    if re.search(r"must\s+(?:have|be)\s+(?:us|u\.s\.)\s+(?:citizen|work authorization|authorized)", lower):
        work_auth = "us_authorized"
    if re.search(r"visa\s+sponsorship\s+not\s+available|no\s+sponsorship", lower):
        work_auth = work_auth or "no_sponsorship"

    return {
        "min_experience_years": float(min_exp) if min_exp is not None else None,
        "min_cgpa": float(min_cgpa) if min_cgpa is not None else None,
        "degree_required": bool(degree_required),
        "locations": locations,
        "work_auth": work_auth,
    }


def evaluate_gates(
    *,
    resume_text: str,
    experience_years: float,
    has_degree: bool,
    education_lines: list[str],
    job_description: str,
    role_meta: dict | None = None,
    candidate_location: str = "",
    candidate_cgpa: float | None = None,
) -> EligibilityReport:
    req = parse_jd_requirements(job_description, role_meta)
    gates: list[GateResult] = []

    # Experience
    min_exp = req.get("min_experience_years")
    if min_exp is not None:
        passed = experience_years + 1e-6 >= min_exp
        gates.append(
            GateResult(
                key="experience",
                label="Minimum experience",
                passed=passed,
                required=f"{min_exp:g}+ years",
                observed=f"{experience_years:g} years detected",
                severity="hard",
                advice=(
                    "This role sets a hard floor on years of experience. "
                    "Skills alone will not override it in most ATS screens."
                    if not passed
                    else "Experience requirement met."
                ),
            )
        )

    # CGPA
    cgpa = candidate_cgpa if candidate_cgpa is not None else extract_cgpa(
        resume_text + "\n" + "\n".join(education_lines)
    )
    min_cgpa = req.get("min_cgpa")
    if min_cgpa is not None:
        if cgpa is None:
            gates.append(
                GateResult(
                    key="cgpa",
                    label="Minimum CGPA / GPA",
                    passed=False,
                    required=f"≥ {min_cgpa} (4.0 scale)",
                    observed="Not found on resume",
                    severity="hard",
                    advice="Add your CGPA/GPA clearly (e.g. CGPA: 3.6/4.0) or you may be auto-filtered.",
                )
            )
        else:
            passed = cgpa + 1e-6 >= min_cgpa
            gates.append(
                GateResult(
                    key="cgpa",
                    label="Minimum CGPA / GPA",
                    passed=passed,
                    required=f"≥ {min_cgpa} (4.0 scale)",
                    observed=f"{cgpa} detected",
                    severity="hard",
                    advice=(
                        "GPA is below the posting's stated cutoff — many campus/ATS pipelines reject here "
                        "even with strong projects."
                        if not passed
                        else "GPA requirement met."
                    ),
                )
            )

    # Degree
    if req.get("degree_required"):
        gates.append(
            GateResult(
                key="degree",
                label="Degree requirement",
                passed=has_degree,
                required="Bachelor's (or equivalent) required",
                observed="Degree signals found" if has_degree else "No degree signal found",
                severity="hard",
                advice=(
                    "List your degree explicitly under Education."
                    if not has_degree
                    else "Degree requirement appears satisfied."
                ),
            )
        )

    # Location
    jd_locations = [x.lower() for x in (req.get("locations") or [])]
    # Filter noise tokens
    jd_locations = [x for x in jd_locations if x not in {"hybrid", "onsite"}]
    must_locations = [x for x in jd_locations if x not in {"remote"}]
    resume_locs = extract_locations(resume_text + " " + candidate_location)
    if must_locations and "remote" not in jd_locations:
        # Require overlap or candidate_location match
        cand = (candidate_location or "").lower()
        overlap = any(
            loc in " ".join(resume_locs) or loc in cand or any(loc in r for r in resume_locs)
            for loc in must_locations
        )
        gates.append(
            GateResult(
                key="location",
                label="Location / onsite constraint",
                passed=overlap,
                required=", ".join(must_locations[:4]),
                observed=", ".join(resume_locs[:4]) or (candidate_location or "Not stated"),
                severity="hard",
                advice=(
                    "Role appears location-bound. If you can relocate or work onsite, state it clearly; "
                    "otherwise this is typically an automatic decline."
                    if not overlap
                    else "Location appears compatible."
                ),
            )
        )
    elif "remote" in jd_locations:
        gates.append(
            GateResult(
                key="location",
                label="Location / remote",
                passed=True,
                required="Remote-friendly",
                observed=", ".join(resume_locs[:4]) or "Not stated",
                severity="soft",
                advice="Role allows remote — location is not a blocker.",
            )
        )

    # Work authorization soft/hard
    if req.get("work_auth") == "us_authorized":
        auth_ok = bool(
            re.search(r"\b(us citizen|authorized to work|green card|h[- ]?1b)\b", resume_text, re.I)
        )
        gates.append(
            GateResult(
                key="work_auth",
                label="Work authorization",
                passed=auth_ok,
                required="US work authorization required",
                observed="Mentioned" if auth_ok else "Not mentioned",
                severity="hard",
                advice=(
                    "Posting requires authorization and often declines sponsorship. "
                    "State your status explicitly if eligible."
                    if not auth_ok
                    else "Work authorization signal found."
                ),
            )
        )

    hard = [g for g in gates if g.severity == "hard" and not g.passed]
    soft = [g for g in gates if g.severity == "soft" and not g.passed]
    soft += [g for g in gates if g.severity == "soft" and g.passed]  # include soft passes as info
    return EligibilityReport(
        eligible=len(hard) == 0,
        gates=gates,
        hard_failures=hard,
        soft_warnings=[g for g in gates if g.severity == "soft"],
    )
