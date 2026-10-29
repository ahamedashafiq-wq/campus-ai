from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.entities import Application, ApplicationStatusHistory, Interview, JobPosting, Resume, StudentProfile
from app.models.enums import (
    ALLOWED_STATUS_TRANSITIONS,
    ApplicationStatus,
    InterviewStatus,
    JobStatus,
    NotificationType,
)
from app.services.audit import audit, notify
from app.services.errors import AppError, Conflict, Forbidden, NotFound
from app.services.job_service import assert_company_access, recruiter_profile
from app.services.match_service import match_student_to_job


def _student(db: Session, user_id: UUID) -> StudentProfile:
    s = db.scalar(
        select(StudentProfile)
        .options(selectinload(StudentProfile.skills), selectinload(StudentProfile.projects), selectinload(StudentProfile.resumes))
        .where(StudentProfile.user_id == user_id)
    )
    if not s:
        raise NotFound("Student profile not found")
    return s


def apply_to_job(db: Session, user_id: UUID, job_id: UUID, cover_note: str | None) -> Application:
    student = _student(db, user_id)
    job = db.scalar(select(JobPosting).options(selectinload(JobPosting.requirements), selectinload(JobPosting.company)).where(JobPosting.id == job_id))
    if not job:
        raise NotFound("Job not found")
    if job.status != JobStatus.published:
        raise AppError("This job is not open for applications", 400, "job_closed")
    if job.application_deadline and job.application_deadline < datetime.now(timezone.utc):
        raise AppError("The application deadline has passed", 400, "deadline")
    existing = db.scalar(select(Application).where(Application.job_id == job_id, Application.student_id == student.id))
    if existing:
        raise Conflict("You have already applied to this job")
    resume = next((r for r in student.resumes if r.is_active), None)
    app = Application(
        job_id=job.id,
        student_id=student.id,
        resume_id=resume.id if resume else None,
        cover_note=cover_note,
        status=ApplicationStatus.applied,
    )
    db.add(app)
    db.flush()
    db.add(
        ApplicationStatusHistory(
            application_id=app.id, from_status=None, to_status=ApplicationStatus.applied, changed_by_user_id=user_id
        )
    )
    match_student_to_job(db, student, job)
    notify(
        db,
        user_id,
        "Application submitted",
        f"Your application for {job.title} was submitted.",
        NotificationType.application_status,
        {"application_id": str(app.id)},
    )
    audit(db, user_id, "application_submit", "application", str(app.id))
    db.commit()
    db.refresh(app)
    return app


def list_student_applications(db: Session, user_id: UUID) -> list[Application]:
    student = _student(db, user_id)
    return list(
        db.scalars(
            select(Application)
            .options(selectinload(Application.job).selectinload(JobPosting.company), selectinload(Application.history), selectinload(Application.interviews))
            .where(Application.student_id == student.id)
            .order_by(Application.submitted_at.desc())
        )
    )


def list_job_applications(db: Session, user_id: UUID, job_id: UUID, *, admin: bool = False) -> list[Application]:
    job = db.get(JobPosting, job_id)
    if not job:
        raise NotFound("Job not found")
    if not admin:
        rec = recruiter_profile(db, user_id)
        assert_company_access(db, rec, job.company_id)
    return list(
        db.scalars(
            select(Application)
            .options(selectinload(Application.student).selectinload(StudentProfile.user), selectinload(Application.history))
            .where(Application.job_id == job_id)
        )
    )


def change_status(db: Session, user_id: UUID, application_id: UUID, new_status: ApplicationStatus, note: str | None, *, as_student: bool = False) -> Application:
    app = db.scalar(
        select(Application)
        .options(selectinload(Application.job), selectinload(Application.student).selectinload(StudentProfile.user))
        .where(Application.id == application_id)
    )
    if not app:
        raise NotFound("Application not found")
    if as_student:
        student = _student(db, user_id)
        if app.student_id != student.id:
            raise Forbidden("You cannot change this application")
        if new_status != ApplicationStatus.withdrawn:
            raise Forbidden("Students may only withdraw applications")
    else:
        rec = recruiter_profile(db, user_id)
        assert_company_access(db, rec, app.job.company_id)
        if new_status == ApplicationStatus.withdrawn:
            raise Forbidden("Recruiters cannot withdraw a student application")
    allowed = ALLOWED_STATUS_TRANSITIONS.get(app.status, set())
    if new_status not in allowed:
        raise AppError(f"Cannot transition from {app.status.value} to {new_status.value}", 400, "invalid_transition")
    old = app.status
    app.status = new_status
    db.add(
        ApplicationStatusHistory(
            application_id=app.id,
            from_status=old,
            to_status=new_status,
            changed_by_user_id=user_id,
            note=note,
        )
    )
    notify(
        db,
        app.student.user_id,
        "Application status updated",
        f"{app.job.title}: {old.value} → {new_status.value}",
        NotificationType.application_status,
        {"application_id": str(app.id), "status": new_status.value},
    )
    audit(db, user_id, "application_status", "application", str(app.id), {"from": old.value, "to": new_status.value})
    db.commit()
    db.refresh(app)
    return app


def schedule_interview(db: Session, user_id: UUID, application_id: UUID, scheduled_at: datetime, location: str | None, notes: str | None) -> Interview:
    app = db.get(Application, application_id)
    if not app:
        raise NotFound("Application not found")
    rec = recruiter_profile(db, user_id)
    job = db.get(JobPosting, app.job_id)
    assert_company_access(db, rec, job.company_id)
    interview = Interview(
        application_id=app.id,
        scheduled_at=scheduled_at,
        location_or_link=location,
        notes=notes,
        status=InterviewStatus.scheduled,
    )
    db.add(interview)
    if app.status in ALLOWED_STATUS_TRANSITIONS and ApplicationStatus.interview_scheduled in ALLOWED_STATUS_TRANSITIONS[app.status]:
        old = app.status
        app.status = ApplicationStatus.interview_scheduled
        db.add(
            ApplicationStatusHistory(
                application_id=app.id,
                from_status=old,
                to_status=ApplicationStatus.interview_scheduled,
                changed_by_user_id=user_id,
                note="Interview scheduled",
            )
        )
    student = db.get(StudentProfile, app.student_id)
    notify(
        db,
        student.user_id,
        "Interview scheduled",
        f"An interview was scheduled for {scheduled_at.isoformat()}",
        NotificationType.interview,
        {"application_id": str(app.id)},
    )
    audit(db, user_id, "interview_schedule", "interview", str(application_id))
    db.commit()
    db.refresh(interview)
    return interview


def update_interview(db: Session, user_id: UUID, interview_id: UUID, **fields) -> Interview:
    interview = db.get(Interview, interview_id)
    if not interview:
        raise NotFound("Interview not found")
    rec = recruiter_profile(db, user_id)
    app = db.get(Application, interview.application_id)
    job = db.get(JobPosting, app.job_id)
    assert_company_access(db, rec, job.company_id)
    for k, v in fields.items():
        if v is not None:
            setattr(interview, k, v)
    if fields.get("scheduled_at") and interview.status == InterviewStatus.scheduled:
        interview.status = InterviewStatus.rescheduled
    db.commit()
    db.refresh(interview)
    return interview
