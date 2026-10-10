"""Alias route matching the plan's GET /sample-jds/{id} path."""

from fastapi import APIRouter, HTTPException

from app.core.schemas import SampleJD
from app.services.roles_loader import get_role

router = APIRouter(prefix="/sample-jds", tags=["sample-jds"])


@router.get("/{role_id}", response_model=SampleJD)
def get_sample_jd(role_id: str):
    role = get_role(role_id)
    if role is None:
        raise HTTPException(status_code=404, detail=f"Unknown sample JD: {role_id}")
    return role
