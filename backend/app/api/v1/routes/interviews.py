from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.entities import Application, Interview, RecruiterProfile, User
from app.models.enums import UserRole
from app.schemas.domain import InterviewCreate, InterviewUpdate
from app.services.application_service import schedule_interview, update_interview
from app.services.job_service import memberships_for, recruiter_profile

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("")
def create(payload: InterviewCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.recruiter))):
    row = schedule_interview(db, user.id, payload.application_id, payload.scheduled_at, payload.location_or_link, payload.notes)
    return {
        "id": row.id,
        "application_id": row.application_id,
        "scheduled_at": row.scheduled_at,
        "location_or_link": row.location_or_link,
        "status": row.status,
        "notes": row.notes,
    }


@router.patch("/{interview_id}")
def patch(interview_id: UUID, payload: InterviewUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.recruiter))):
    row = update_interview(db, user.id, interview_id, **payload.model_dump(exclude_unset=True))
    return {
        "id": row.id,
        "application_id": row.application_id,
        "scheduled_at": row.scheduled_at,
        "location_or_link": row.location_or_link,
        "status": row.status,
        "notes": row.notes,
    }


@router.get("")
def list_interviews(db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.recruiter, UserRole.student, UserRole.admin))):
    if user.role == UserRole.student:
        from app.models.entities import StudentProfile

        student = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
        rows = list(
            db.scalars(
                select(Interview)
                .join(Application, Interview.application_id == Application.id)
                .where(Application.student_id == student.id)
            )
        )
    elif user.role == UserRole.recruiter:
        rec = recruiter_profile(db, user.id)
        company_ids = [m.company_id for m in memberships_for(db, rec.id)]
        from app.models.entities import JobPosting

        rows = list(
            db.scalars(
                select(Interview)
                .join(Application, Interview.application_id == Application.id)
                .join(JobPosting, Application.job_id == JobPosting.id)
                .where(JobPosting.company_id.in_(company_ids))
            )
        )
    else:
        rows = list(db.scalars(select(Interview)))
    return [
        {
            "id": r.id,
            "application_id": r.application_id,
            "scheduled_at": r.scheduled_at,
            "location_or_link": r.location_or_link,
            "status": r.status,
            "notes": r.notes,
        }
        for r in rows
    ]
