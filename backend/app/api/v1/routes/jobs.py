from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.entities import User
from app.models.enums import JobStatus, UserRole
from app.schemas.domain import JobCreate, JobOut, JobUpdate
from app.services.job_service import create_job, get_job, job_to_dict, search_jobs, update_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("")
def list_jobs(
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: JobStatus | None = JobStatus.published,
    company_id: UUID | None = None,
    db: Session = Depends(get_db),
):
    rows, total = search_jobs(db, q=q, status=status, page=page, page_size=page_size, company_id=company_id)
    return {"items": [job_to_dict(j) for j in rows], "total": total, "page": page, "page_size": page_size}


@router.get("/{job_id}")
def job_detail(job_id: UUID, db: Session = Depends(get_db)):
    return job_to_dict(get_job(db, job_id))


@router.post("")
def create(payload: JobCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.recruiter))):
    job = create_job(db, user.id, payload)
    return job_to_dict(get_job(db, job.id))


@router.patch("/{job_id}")
def patch(job_id: UUID, payload: JobUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.recruiter))):
    job = update_job(db, user.id, job_id, payload)
    return job_to_dict(get_job(db, job.id))


@router.post("/{job_id}/publish")
def publish(job_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.recruiter))):
    return job_to_dict(update_job(db, user.id, job_id, JobUpdate(status=JobStatus.published)))


@router.post("/{job_id}/close")
def close(job_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.recruiter))):
    return job_to_dict(update_job(db, user.id, job_id, JobUpdate(status=JobStatus.closed)))


@router.post("/{job_id}/archive")
def archive(job_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.recruiter))):
    return job_to_dict(update_job(db, user.id, job_id, JobUpdate(status=JobStatus.archived)))
