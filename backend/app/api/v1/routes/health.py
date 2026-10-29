from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.ai.embeddings import embedding_status
from app.config import get_settings
from app.db.session import get_db
from app.storage import get_storage
from app.services.emailer import email_status

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    s = get_settings()
    return {"status": "ok", "app": s.app_name, "environment": s.app_env}


@router.get("/health/ready")
def ready(db: Session = Depends(get_db)):
    s = get_settings()
    db_ok = False
    db_error = None
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:
        db_error = str(exc)[:200]
    storage = get_storage().health()
    matching = embedding_status()
    overall = "ok" if db_ok and storage.get("writable", True) else "degraded"
    payload = {
        "status": overall,
        "app": s.app_name,
        "environment": s.app_env,
        "database": {"ok": db_ok, "error": db_error},
        "storage": storage,
        "matching": matching,
        "email": email_status(),
        "llm": {"provider": s.llm_provider, "configured": s.llm_provider != "none" and bool(s.llm_api_key)},
    }
    return JSONResponse(payload, status_code=200 if db_ok else 503)
