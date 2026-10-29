"""Explicit development fixtures. Never run in production. Labeled as synthetic."""

from sqlalchemy.orm import Session

from app.models.entities import User
from app.models.enums import UserRole
from app.schemas.auth import RegisterRecruiterIn, RegisterStudentIn
from app.schemas.domain import JobCreate
from app.services.auth_service import get_user_by_email, register_recruiter, register_student
from app.services.job_service import create_job, update_job
from app.models.enums import JobStatus
from app.schemas.domain import JobUpdate


def seed_development_data(db: Session) -> None:
    if not get_user_by_email(db, "dev.student@example.com"):
        register_student(
            db,
            RegisterStudentIn(
                email="dev.student@example.com",
                password="DevPass123!",
                full_name="[DEV] Sample Student",
                department="Computer Science",
                degree="B.Tech",
                graduation_year=2026,
            ),
        )
    if not get_user_by_email(db, "dev.recruiter@example.com"):
        rec = register_recruiter(
            db,
            RegisterRecruiterIn(
                email="dev.recruiter@example.com",
                password="DevPass123!",
                full_name="[DEV] Sample Recruiter",
                company_name="[DEV] Example Labs",
                company_website="https://example.com",
                title="University Recruiter",
            ),
        )
        job = create_job(
            db,
            rec.id,
            JobCreate(
                title="[DEV] Junior Software Engineer",
                description="Development fixture job for local testing of CampusMatch AI matching. Not a real opening.",
                responsibilities="Build features, write tests, collaborate with mentors.",
                location="Remote",
                employment_type="Internship",
                required_skills=["Python", "SQL", "Git"],
                preferred_skills=["FastAPI", "React"],
            ),
        )
        update_job(db, rec.id, job.id, JobUpdate(status=JobStatus.published))
