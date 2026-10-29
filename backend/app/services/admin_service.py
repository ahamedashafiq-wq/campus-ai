from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import (
    Application,
    AuditLog,
    Company,
    JobPosting,
    PlacementDrive,
    PlacementDriveJob,
    StudentProfile,
    StudentSkill,
    User,
)
from app.models.enums import ApplicationStatus, CompanyVerification, JobStatus, UserRole
from app.services.audit import audit
from app.services.errors import NotFound


def set_user_active(db: Session, admin_id: UUID, user_id: UUID, active: bool) -> User:
    user = db.get(User, user_id)
    if not user:
        raise NotFound("User not found")
    user.is_active = active
    audit(db, admin_id, "user_active" if active else "user_disable", "user", str(user_id))
    db.commit()
    return user


def verify_company(db: Session, admin_id: UUID, company_id: UUID, status: CompanyVerification, notes: str | None) -> Company:
    company = db.get(Company, company_id)
    if not company:
        raise NotFound("Company not found")
    company.verification_status = status
    company.verification_notes = notes
    audit(db, admin_id, "company_verify", "company", str(company_id), {"status": status.value})
    db.commit()
    return company


def create_drive(db: Session, admin_id: UUID, title: str, description: str | None, starts_at, ends_at, job_ids: list[UUID]) -> PlacementDrive:
    drive = PlacementDrive(title=title, description=description, starts_at=starts_at, ends_at=ends_at)
    db.add(drive)
    db.flush()
    for jid in job_ids:
        db.add(PlacementDriveJob(drive_id=drive.id, job_id=jid))
    audit(db, admin_id, "drive_create", "placement_drive", str(drive.id))
    db.commit()
    db.refresh(drive)
    return drive


def analytics(db: Session) -> dict:
    users_by_role = {
        role.value: db.scalar(select(func.count()).where(User.role == role)) or 0 for role in UserRole
    }
    apps_by_status = {
        st.value: db.scalar(select(func.count()).where(Application.status == st)) or 0 for st in ApplicationStatus
    }
    jobs_by_status = {
        st.value: db.scalar(select(func.count()).where(JobPosting.status == st)) or 0 for st in JobStatus
    }
    dept_rows = db.execute(
        select(StudentProfile.department, func.count())
        .where(StudentProfile.department.is_not(None))
        .group_by(StudentProfile.department)
    ).all()
    skill_rows = db.execute(
        select(StudentSkill.skill_name, func.count()).group_by(StudentSkill.skill_name).order_by(func.count().desc()).limit(20)
    ).all()
    return {
        "users_by_role": users_by_role,
        "applications_by_status": apps_by_status,
        "jobs_by_status": jobs_by_status,
        "students_by_department": [{"department": d or "Unknown", "count": c} for d, c in dept_rows],
        "top_skills": [{"skill": n, "count": c} for n, c in skill_rows],
        "totals": {
            "users": db.scalar(select(func.count()).select_from(User)) or 0,
            "jobs": db.scalar(select(func.count()).select_from(JobPosting)) or 0,
            "applications": db.scalar(select(func.count()).select_from(Application)) or 0,
            "companies": db.scalar(select(func.count()).select_from(Company)) or 0,
        },
    }


def list_audit(db: Session, limit: int = 100) -> list[AuditLog]:
    return list(db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)))
