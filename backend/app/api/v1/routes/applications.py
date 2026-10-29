from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.entities import Application, JobMatch, JobPosting, User
from app.models.enums import UserRole
from app.schemas.domain import ApplicationCreate, ApplicationStatusIn
from app.services.application_service import apply_to_job, change_status, list_job_applications, list_student_applications
from app.services.job_service import job_to_dict

router = APIRouter(prefix="/applications", tags=["applications"])


def _app_out(app: Application, match: dict | None = None) -> dict:
    return {
        "id": app.id,
        "job_id": app.job_id,
        "student_id": app.student_id,
        "status": app.status,
        "cover_note": app.cover_note,
        "submitted_at": app.submitted_at,
        "job_title": app.job.title if app.job else None,
        "company_name": app.job.company.name if app.job and app.job.company else None,
        "student_name": app.student.user.full_name if getattr(app, "student", None) and app.student.user else None,
        "history": [
            {
                "from_status": h.from_status,
                "to_status": h.to_status,
                "note": h.note,
                "created_at": h.created_at,
            }
            for h in (app.history or [])
        ],
        "match": match,
    }


@router.post("")
def apply(payload: ApplicationCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.student))):
    app = apply_to_job(db, user.id, payload.job_id, payload.cover_note)
    app = db.scalar(
        select(Application)
        .options(selectinload(Application.job).selectinload(JobPosting.company), selectinload(Application.history))
        .where(Application.id == app.id)
    )
    return _app_out(app)


@router.get("/me")
def mine(db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.student))):
    rows = list_student_applications(db, user.id)
    return [_app_out(a) for a in rows]


@router.post("/{application_id}/withdraw")
def withdraw(application_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.student))):
    from app.models.enums import ApplicationStatus

    app = change_status(db, user.id, application_id, ApplicationStatus.withdrawn, None, as_student=True)
    return {"id": app.id, "status": app.status}


@router.get("/jobs/{job_id}")
def for_job(job_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.recruiter, UserRole.admin))):
    rows = list_job_applications(db, user.id, job_id, admin=user.role == UserRole.admin)
    out = []
    for a in rows:
        match = db.scalar(select(JobMatch).where(JobMatch.job_id == a.job_id, JobMatch.student_id == a.student_id))
        out.append(_app_out(a, match.explanation if match else None))
    return out


@router.post("/{application_id}/status")
def set_status(
    application_id: UUID,
    payload: ApplicationStatusIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.recruiter, UserRole.admin)),
):
    app = change_status(db, user.id, application_id, payload.status, payload.note, as_student=False)
    return {"id": app.id, "status": app.status}
