from fastapi import APIRouter

from app.services.scorer import load_model_bundle

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    bundle = load_model_bundle()
    return {
        "status": "ok",
        "model_loaded": bundle is not None,
        "model_name": (bundle or {}).get("model_name", "heuristic_fallback"),
    }
