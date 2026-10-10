"""Job feed endpoints — curated market JDs + live Remotive cache/refresh."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.core.schemas import JobFeedItem, SampleJD
from app.services.job_feed import get_job, job_as_sample, list_job_feed

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/feed", response_model=List[JobFeedItem])
def job_feed(
    level: str = Query("all", description="entry | mid | senior | all"),
    source: str = Query("all", description="curated | live | all"),
    refresh: bool = Query(False, description="Attempt live Remotive refresh"),
):
    level = level.lower().strip()
    source = source.lower().strip()
    if level not in {"all", "entry", "mid", "senior"}:
        raise HTTPException(status_code=400, detail="level must be entry|mid|senior|all")
    if source not in {"all", "curated", "live"}:
        raise HTTPException(status_code=400, detail="source must be curated|live|all")
    return list_job_feed(level=level, source=source, refresh_live=refresh)


@router.get("/{job_id}", response_model=SampleJD)
def get_job_detail(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Unknown job_id: {job_id}")
    sample = job_as_sample(job)
    sample.experience_level = job.experience_level
    sample.company = job.company
    sample.source = job.source
    sample.source_url = job.source_url
    return sample
