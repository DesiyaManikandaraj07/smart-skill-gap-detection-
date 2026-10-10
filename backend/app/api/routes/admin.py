"""Admin panel API — users, analyses, model stats."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.config import settings
from app.core.schemas import AdminStats, AnalysisListItem, UserOut
from app.db.models import Analysis, User
from app.db.session import get_db
from app.services.scorer import load_model_bundle

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStats)
def stats(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    users_total = db.query(func.count(User.id)).scalar() or 0
    analyses_total = db.query(func.count(Analysis.id)).scalar() or 0
    today = datetime.now(timezone.utc).date()
    analyses_today = (
        db.query(func.count(Analysis.id))
        .filter(func.date(Analysis.created_at) == today)
        .scalar()
        or 0
    )
    avg = db.query(func.avg(Analysis.selection_likelihood_pct)).scalar() or 0.0
    ineligible = db.query(func.count(Analysis.id)).filter(Analysis.eligible.is_(False)).scalar() or 0
    ineligible_rate = (ineligible / analyses_total) if analyses_total else 0.0

    bundle = load_model_bundle() or {}
    metrics_path = settings.processed_dir / "metrics.json"
    metrics = {}
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

    return AdminStats(
        users_total=users_total,
        analyses_total=analyses_total,
        analyses_today=analyses_today,
        avg_selection_pct=round(float(avg), 2),
        ineligible_rate=round(float(ineligible_rate), 4),
        model_name=bundle.get("model_name", "heuristic_fallback"),
        model_metrics=metrics,
    )


@router.get("/users", response_model=list[UserOut])
def list_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).limit(500).all()
    return [UserOut.model_validate(u) for u in users]


@router.patch("/users/{user_id}/toggle-active", response_model=UserOut)
def toggle_active(user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.get("/analyses", response_model=list[AnalysisListItem])
def list_analyses(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = (
        db.query(Analysis, User.email)
        .join(User, User.id == Analysis.user_id)
        .order_by(Analysis.created_at.desc())
        .limit(200)
        .all()
    )
    out: list[AnalysisListItem] = []
    for analysis, email in rows:
        payload = analysis.result_json or {}
        out.append(
            AnalysisListItem(
                id=analysis.id,
                user_email=email,
                candidate_name=analysis.candidate_name,
                role_title=analysis.role_title,
                selection_likelihood_pct=analysis.selection_likelihood_pct,
                effective_selection_pct=float(payload.get("effective_selection_pct", analysis.selection_likelihood_pct)),
                eligible=analysis.eligible,
                created_at=analysis.created_at,
            )
        )
    return out
