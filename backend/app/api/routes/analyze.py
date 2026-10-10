from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_optional_user
from app.core.config import settings
from app.core.schemas import AnalyzeResponse, WhatIfRequest, WhatIfResponse
from app.db.models import Analysis, User
from app.db.session import get_db
from app.services.pdf_parser import PDFParseError
from app.services.pipeline import analyze_resume, run_what_if

router = APIRouter(tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    file: UploadFile = File(..., description="Resume PDF"),
    name: str = Form(..., description="Candidate display name"),
    extra_skills: str = Form(""),
    role_id: str = Form(""),
    job_description: str = Form(""),
    location: str = Form(""),
    cgpa: str = Form(""),
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported.")

    data = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File too large. Max {settings.max_upload_mb} MB.")

    rid = role_id.strip() or None
    jd = job_description.strip()
    if not rid and not jd:
        raise HTTPException(status_code=400, detail="Provide role_id and/or a custom job_description.")

    cgpa_val = None
    if cgpa.strip():
        try:
            cgpa_val = float(cgpa.strip())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="cgpa must be a number") from exc

    try:
        result = analyze_resume(
            pdf_bytes=data,
            candidate_name=name,
            extra_skills=extra_skills,
            role_id=rid,
            job_description=jd,
            candidate_location=location,
            candidate_cgpa=cgpa_val,
        )
    except PDFParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc

    # Persist when authenticated
    if user is not None:
        row = Analysis(
            user_id=user.id,
            candidate_name=result.candidate_name,
            role_id=result.role_id,
            role_title=result.role_title,
            selection_likelihood_pct=result.selection_likelihood_pct,
            confidence=result.confidence,
            eligible=result.eligible,
            gate_failures=len(result.summary.critical_blockers) if result.summary else 0,
            result_json=result.model_dump(mode="json"),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        result.id = row.id

    return result


@router.get("/analyses/mine", response_model=List[AnalyzeResponse])
def my_analyses(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Analysis)
        .filter(Analysis.user_id == user.id)
        .order_by(Analysis.created_at.desc())
        .limit(50)
        .all()
    )
    out: List[AnalyzeResponse] = []
    for row in rows:
        payload = dict(row.result_json or {})
        payload["id"] = row.id
        out.append(AnalyzeResponse.model_validate(payload))
    return out


@router.post("/what-if", response_model=WhatIfResponse)
def what_if(body: WhatIfRequest):
    if not body.job_skills:
        raise HTTPException(status_code=400, detail="job_skills is required.")
    try:
        return run_what_if(body)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"What-if failed: {exc}") from exc
