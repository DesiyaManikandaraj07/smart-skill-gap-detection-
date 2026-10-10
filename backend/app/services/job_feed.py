"""Job feed: curated market JDs + cached/live Remotive postings."""

from __future__ import annotations

import html
import json
import re
from functools import lru_cache
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings
from app.core.schemas import JobFeedItem, SampleJD

SKILL_MAP = {
    "python": "Python",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "react": "React",
    "node": "Node.js",
    "java": "Java",
    "golang": "Go",
    "go": "Go",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "aws": "Amazon Web Services",
    "azure": "Microsoft Azure",
    "sql": "SQL",
    "postgresql": "PostgreSQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "django": "Django",
    "fastapi": "FastAPI",
    "terraform": "Terraform",
    "linux": "Linux",
    "git": "Git",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "pandas": "Pandas",
    "graphql": "GraphQL",
    "next.js": "Next.js",
    "vue": "Vue.js",
    "angular": "Angular",
    "security": "Cybersecurity",
    "html": "HTML",
    "css": "CSS",
    "api": "REST API",
}


def _strip_html(s: str) -> str:
    text = re.sub(r"<[^>]+>", "\n", s or "")
    text = html.unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _infer_level(title: str, desc: str) -> str:
    t = f"{title} {desc[:800]}".lower()
    if re.search(r"\b(intern|internship|graduate|new grad|entry[- ]level|junior|jr\.?|campus|associate)\b", t):
        return "entry"
    if re.search(r"\b(staff|principal|lead|architect)\b", t):
        return "senior"
    if re.search(r"\b(senior|sr\.?)\b", t):
        return "senior"
    if re.search(r"\b(mid[- ]level|intermediate)\b", t):
        return "mid"
    m = re.search(r"(\d+)\+?\s*(?:years?|yrs?)", t)
    if m:
        y = int(m.group(1))
        if y <= 2:
            return "entry"
        if y >= 5:
            return "senior"
        return "mid"
    return "mid"


def _extract_skills(tags: list[str], desc: str) -> list[str]:
    found: list[str] = []
    blob = " ".join(tags).lower() + " " + (desc or "").lower()
    for key, canon in SKILL_MAP.items():
        if re.search(rf"(?<![a-z]){re.escape(key)}(?![a-z])", blob) and canon not in found:
            found.append(canon)
    return found[:14]


def _to_item(raw: dict[str, Any]) -> JobFeedItem:
    return JobFeedItem(
        id=raw["id"],
        title=raw["title"],
        company=raw.get("company") or "Employer",
        category=raw.get("category") or "Tech",
        experience_level=raw.get("experience_level") or "mid",
        summary=raw.get("summary") or "",
        description=raw.get("description") or "",
        required_skills=list(raw.get("required_skills") or []),
        min_experience_years=raw.get("min_experience_years"),
        min_cgpa=raw.get("min_cgpa"),
        degree_required=bool(raw.get("degree_required", True)),
        locations=list(raw.get("locations") or []),
        source=raw.get("source") or "curated",
        source_url=raw.get("source_url") or "",
        posted_at=raw.get("posted_at") or "",
        salary=raw.get("salary") or "",
    )


@lru_cache(maxsize=1)
def _load_curated() -> list[dict]:
    path = settings.sample_jds_dir / "curated_job_feed.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_live_cache() -> list[dict]:
    path = settings.sample_jds_dir / "live_feed_cache.json"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _fetch_remotive(limit: int = 40) -> list[dict]:
    """Best-effort live pull; returns [] on network/403 failures."""
    url = f"https://remotive.com/api/remote-jobs?category=software-dev&limit={limit}"
    req = Request(
        url,
        headers={
            "User-Agent": "ArawindSkillGap/2.0 (academic demo; +https://localhost)",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(req, timeout=12) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return []

    skip = ("writer", "copywriter", "content reviewer", "office assistant")
    out: list[dict] = []
    for j in payload.get("jobs", []):
        title = (j.get("title") or "").strip()
        if not title or any(s in title.lower() for s in skip):
            continue
        desc = _strip_html(j.get("description") or "")
        if len(desc) < 180:
            continue
        if len(desc) > 4500:
            desc = desc[:4500] + "\n\n[Truncated for demo feed]"
        level = _infer_level(title, desc)
        skills = _extract_skills(list(j.get("tags") or []), desc)
        if len(skills) < 3:
            skills = list(dict.fromkeys([t.title() for t in (j.get("tags") or [])[:8]]))
        out.append(
            {
                "id": f"live-{j.get('id')}",
                "title": title,
                "company": j.get("company_name") or "Remote employer",
                "category": j.get("category") or "Software Development",
                "experience_level": level,
                "summary": (desc[:150].rsplit(" ", 1)[0] + "…") if len(desc) > 150 else desc,
                "description": (
                    f"{title} — {j.get('company_name')}\n\n"
                    f"Location: {j.get('candidate_required_location') or 'Remote'}\n"
                    f"Source: Remotive live feed\n"
                    f"Posted: {j.get('publication_date') or 'n/a'}\n"
                    f"Apply: {j.get('url') or ''}\n\n{desc}"
                ),
                "required_skills": skills[:14],
                "min_experience_years": {"entry": 0.0, "mid": 2.0, "senior": 5.0}.get(level, 2.0),
                "min_cgpa": None,
                "degree_required": True,
                "locations": ["remote"],
                "source": "remotive_live",
                "source_url": j.get("url") or "",
                "posted_at": j.get("publication_date") or "",
                "salary": j.get("salary") or "",
            }
        )
    return out


def list_job_feed(
    *,
    level: str = "all",
    source: str = "all",
    refresh_live: bool = False,
) -> list[JobFeedItem]:
    curated = list(_load_curated())
    live = list(_load_live_cache())
    if refresh_live:
        fetched = _fetch_remotive()
        if fetched:
            live = fetched
            # refresh on-disk cache for offline demos
            cache_path = settings.sample_jds_dir / "live_feed_cache.json"
            cache_path.write_text(json.dumps(fetched, indent=2), encoding="utf-8")
            _load_live_cache.cache_clear()

    rows: list[dict] = []
    if source in {"all", "curated"}:
        rows.extend(curated)
    if source in {"all", "live"}:
        rows.extend(live)

    # de-dupe by id
    seen: set[str] = set()
    unique: list[dict] = []
    for r in rows:
        rid = r.get("id")
        if not rid or rid in seen:
            continue
        seen.add(rid)
        unique.append(r)

    level_norm = (level or "all").lower()
    if level_norm in {"entry", "mid", "senior"}:
        unique = [r for r in unique if (r.get("experience_level") or "").lower() == level_norm]

    # Sort: curated first, then by level order, then title
    level_rank = {"entry": 0, "mid": 1, "senior": 2}
    unique.sort(
        key=lambda r: (
            0 if r.get("source", "").startswith("curated") else 1,
            level_rank.get(r.get("experience_level", "mid"), 9),
            r.get("title", ""),
        )
    )
    return [_to_item(r) for r in unique]


def get_job(job_id: str) -> Optional[JobFeedItem]:
    for item in list_job_feed(level="all", source="all", refresh_live=False):
        if item.id == job_id:
            return item
    return None


def job_as_sample(job: JobFeedItem) -> SampleJD:
    return SampleJD(
        id=job.id,
        title=job.title,
        category=job.category,
        description=job.description,
        required_skills=job.required_skills,
        min_experience_years=job.min_experience_years,
        min_cgpa=job.min_cgpa,
        degree_required=job.degree_required,
        locations=job.locations,
    )
