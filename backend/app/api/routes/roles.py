from fastapi import APIRouter, HTTPException

from app.core.schemas import RoleSummary, SampleJD
from app.services.roles_loader import get_role, list_roles

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=list[RoleSummary])
def get_roles():
    return list_roles()


@router.get("/{role_id}", response_model=SampleJD)
def get_sample_jd(role_id: str):
    role = get_role(role_id)
    if role is None:
        raise HTTPException(status_code=404, detail=f"Unknown role_id: {role_id}")
    return role
