"""Resume NLP: skill extraction + lightweight section parsing.

Uses spaCy when available; always falls back to taxonomy dictionary matching
so the demo runs even before `en_core_web_sm` is installed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.services.taxonomy import catalog_skills_sorted, normalize_many, normalize_skill

_NLP = None
_NLP_LOAD_ATTEMPTED = False


def _get_nlp():
    global _NLP, _NLP_LOAD_ATTEMPTED
    if _NLP_LOAD_ATTEMPTED:
        return _NLP
    _NLP_LOAD_ATTEMPTED = True
    try:
        import spacy

        try:
            _NLP = spacy.load("en_core_web_sm")
        except OSError:
            # Minimal blank English pipeline if model missing
            _NLP = spacy.blank("en")
            _NLP.add_pipe("sentencizer")
    except Exception:  # noqa: BLE001
        _NLP = None
    return _NLP


SECTION_HEADERS = {
    "skills": re.compile(r"^(skills|technical skills|tech stack|technologies)\b", re.I),
    "education": re.compile(r"^(education|academic|qualifications)\b", re.I),
    "projects": re.compile(r"^(projects|personal projects|academic projects)\b", re.I),
    "experience": re.compile(
        r"^(experience|work experience|employment|professional experience)\b", re.I
    ),
    "internships": re.compile(r"^(internships?|internship experience)\b", re.I),
    "certifications": re.compile(r"^(certifications?|certificates|licenses)\b", re.I),
}


@dataclass
class StructuredResume:
    skills: list[str] = field(default_factory=list)
    education: list[str] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)
    internships: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    experience_years: float = 0.0
    cgpa: float | None = None
    locations: list[str] = field(default_factory=list)
    raw_text: str = ""


def _split_sections(text: str) -> dict[str, str]:
    lines = text.splitlines()
    sections: dict[str, list[str]] = {k: [] for k in SECTION_HEADERS}
    current: str | None = None
    preamble: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        matched_header = None
        for name, pattern in SECTION_HEADERS.items():
            if pattern.match(stripped.rstrip(":")) or pattern.match(
                stripped.split(":")[0].strip()
            ):
                matched_header = name
                break
        if matched_header:
            current = matched_header
            # Keep residual after colon on same line
            after = stripped.split(":", 1)
            if len(after) == 2 and after[1].strip():
                sections[current].append(after[1].strip())
            continue
        if current:
            sections[current].append(stripped)
        else:
            preamble.append(stripped)

    sections["preamble"] = preamble  # type: ignore[assignment]
    return {k: "\n".join(v) if isinstance(v, list) else v for k, v in sections.items()}


def _dictionary_skills(text: str) -> list[str]:
    """Scan text for catalog skills (longest-first to prefer 'React Native' over 'React')."""
    lower = text.lower()
    found: list[str] = []
    occupied = [False] * len(lower)
    skills = sorted(catalog_skills_sorted(), key=lambda s: len(s), reverse=True)
    for skill in skills:
        pattern = re.compile(rf"(?<![a-z0-9]){re.escape(skill.lower())}(?![a-z0-9])", re.I)
        for m in pattern.finditer(lower):
            if any(occupied[m.start() : m.end()]):
                continue
            for i in range(m.start(), m.end()):
                occupied[i] = True
            found.append(skill)
            break
    return normalize_many(found)


def _lines_as_bullets(block: str, limit: int = 12) -> list[str]:
    out: list[str] = []
    for line in block.splitlines():
        cleaned = re.sub(r"^[\-\*\u2022\d\.\)\s]+", "", line).strip()
        if len(cleaned) >= 8:
            out.append(cleaned[:200])
        if len(out) >= limit:
            break
    return out


def _estimate_experience_years(text: str) -> float:
    patterns = [
        re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+(?:of\s+)?experience", re.I),
        re.compile(r"experience\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*\+?\s*years?", re.I),
    ]
    years: list[float] = []
    for pat in patterns:
        for m in pat.finditer(text):
            try:
                years.append(float(m.group(1)))
            except ValueError:
                continue
    # Date-range heuristic: 2020 – 2023
    range_pat = re.compile(r"(20\d{2})\s*[–\-to]+\s*(20\d{2}|present|current)", re.I)
    spans = []
    for m in range_pat.finditer(text):
        start = int(m.group(1))
        end_raw = m.group(2).lower()
        end = 2025 if end_raw in {"present", "current"} else int(end_raw)
        if end >= start:
            spans.append(end - start)
    if years:
        return min(max(years), 40.0)
    if spans:
        return float(min(sum(spans), 40))
    return 0.0


def extract_structured_resume(text: str, extra_skills: str = "") -> StructuredResume:
    sections = _split_sections(text)
    skill_blob = sections.get("skills", "") + "\n" + text
    skills = _dictionary_skills(skill_blob)
    skills = normalize_many(skills + _split_extra(extra_skills))

    # spaCy NER pass — collect ORG/PRODUCT-like tokens that normalize to skills
    nlp = _get_nlp()
    if nlp is not None:
        try:
            doc = nlp(text[:20000])
            ner_skills = []
            for ent in getattr(doc, "ents", []):
                canon = normalize_skill(ent.text)
                if canon:
                    ner_skills.append(canon)
            skills = normalize_many(skills + ner_skills)
        except Exception:  # noqa: BLE001
            pass

    education = _lines_as_bullets(sections.get("education", ""), limit=8)
    projects = _lines_as_bullets(sections.get("projects", ""), limit=10)
    internships = _lines_as_bullets(sections.get("internships", ""), limit=8)
    certifications = _lines_as_bullets(sections.get("certifications", ""), limit=8)

    # Heuristic certification keywords
    cert_hits = re.findall(
        r"\b(?:AWS|Azure|Google Cloud|CKA|CompTIA|PMP|Cisco|Oracle|Meta)\b[^\n,]{0,40}",
        text,
        flags=re.I,
    )
    for c in cert_hits:
        if c.strip() not in certifications:
            certifications.append(c.strip()[:120])

    from app.services.hard_gates import extract_cgpa, extract_locations

    return StructuredResume(
        skills=skills,
        education=education,
        projects=projects,
        internships=internships,
        certifications=certifications[:10],
        experience_years=_estimate_experience_years(text),
        cgpa=extract_cgpa(text + "\n" + "\n".join(education)),
        locations=extract_locations(text),
        raw_text=text,
    )


def _split_extra(extra_skills: str) -> list[str]:
    if not extra_skills:
        return []
    parts = re.split(r"[,;\n|/]+", extra_skills)
    return [p.strip() for p in parts if p.strip()]
