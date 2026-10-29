from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.entities import JobPosting, StudentProfile, User
from app.models.enums import UserRole
from app.services.errors import Forbidden, NotFound
from app.services.job_service import assert_company_access, job_to_dict, recruiter_profile
from app.services.match_service import match_for_ids, match_student_to_job, recommend_jobs_for_student

router = APIRouter(prefix="/matches", tags=["matching"])


@router.get("/recommendations")
def recommendations(db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.student))):
    ranked = recommend_jobs_for_student(db, user.id)
    return [{"job": job_to_dict(item["job"]), "match": item["match"]} for item in ranked]


@router.get("/jobs/{job_id}/me")
def match_me(job_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.student))):
    student = db.scalar(
        select(StudentProfile)
        .options(selectinload(StudentProfile.skills), selectinload(StudentProfile.projects), selectinload(StudentProfile.resumes))
        .where(StudentProfile.user_id == user.id)
    )
    if not student:
        raise NotFound("Student profile not found")
    job = db.scalar(select(JobPosting).options(selectinload(JobPosting.requirements), selectinload(JobPosting.company)).where(JobPosting.id == job_id))
    if not job:
        raise NotFound("Job not found")
    result = match_student_to_job(db, student, job)
    return {"job": job_to_dict(job), "match": result}


@router.get("/jobs/{job_id}/students/{student_id}")
def match_recruiter(
    job_id: UUID,
    student_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.recruiter, UserRole.admin)),
):
    if user.role == UserRole.recruiter:
        rec = recruiter_profile(db, user.id)
        job = db.get(JobPosting, job_id)
        if not job:
            raise NotFound("Job not found")
        assert_company_access(db, rec, job.company_id)
    return match_for_ids(db, student_id, job_id)
