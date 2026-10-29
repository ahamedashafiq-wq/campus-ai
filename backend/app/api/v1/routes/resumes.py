from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.entities import Resume, User
from app.models.enums import UserRole
from app.services.resume_service import delete_resume, get_resume_for_user, list_resumes, load_resume_bytes, upload_resume

router = APIRouter(prefix="/resumes", tags=["resumes"])


def _resume_out(r: Resume) -> dict:
    extraction = None
    if r.extraction:
        extraction = {
            "char_count": r.extraction.char_count,
            "extracted_skills": r.extraction.extracted_skills,
            "education": r.extraction.education,
            "experience": r.extraction.experience,
            "projects": r.extraction.projects,
            "certifications": r.extraction.certifications,
            "links": r.extraction.links,
            "completeness": r.extraction.completeness,
            "uncertain_fields": r.extraction.uncertain_fields,
            "extraction_notes": r.extraction.extraction_notes,
            "has_raw_text": bool(r.extraction.raw_text),
        }
    return {
        "id": r.id,
        "original_filename": r.original_filename,
        "content_type": r.content_type,
        "size_bytes": r.size_bytes,
        "status": r.status,
        "is_active": r.is_active,
        "error_message": r.error_message,
        "created_at": r.created_at,
        "extraction": extraction,
    }


@router.post("")
def upload(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.student))):
    data = file.file.read()
    resume = upload_resume(db, user.id, file.filename or "resume.pdf", file.content_type or "application/pdf", data)
    resume = db.get(Resume, resume.id)
    db.refresh(resume)
    resume = db.execute(
        __import__("sqlalchemy").select(Resume).options(selectinload(Resume.extraction)).where(Resume.id == resume.id)
    ).scalar_one()
    return _resume_out(resume)


@router.get("")
def list_mine(db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.student))):
    from sqlalchemy import select

    rows = list_resumes(db, user.id)
    ids = [r.id for r in rows]
    if not ids:
        return []
    loaded = list(db.scalars(select(Resume).options(selectinload(Resume.extraction)).where(Resume.id.in_(ids))))
    loaded.sort(key=lambda r: r.created_at, reverse=True)
    return [_resume_out(r) for r in loaded]


@router.get("/{resume_id}")
def get_one(resume_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from sqlalchemy import select

    get_resume_for_user(
        db,
        user.id,
        resume_id,
        admin=user.role == UserRole.admin,
        recruiter=user.role == UserRole.recruiter,
    )
    r = db.scalar(select(Resume).options(selectinload(Resume.extraction)).where(Resume.id == resume_id))
    return _resume_out(r)


@router.get("/{resume_id}/file")
def download(resume_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    resume = get_resume_for_user(
        db,
        user.id,
        resume_id,
        admin=user.role == UserRole.admin,
        recruiter=user.role == UserRole.recruiter,
    )
    data = load_resume_bytes(resume)
    return Response(content=data, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=resume.pdf", "X-Content-Type-Options": "nosniff"})


@router.delete("/{resume_id}")
def remove(resume_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.student))):
    delete_resume(db, user.id, resume_id)
    return {"deleted": True}
