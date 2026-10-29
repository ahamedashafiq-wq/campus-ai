from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.entities import Company, JobPosting, PlacementDrive, RecruiterProfile, User
from app.models.enums import CompanyVerification, UserRole
from app.schemas.domain import DriveCreate
from app.services import admin_service
from app.services.job_service import job_to_dict, search_jobs

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def users(db: Session = Depends(get_db), admin: User = Depends(require_roles(UserRole.admin))):
    rows = list(db.scalars(select(User).order_by(User.created_at.desc())))
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": u.is_active,
            "email_verified": u.email_verified,
        }
        for u in rows
    ]


@router.post("/users/{user_id}/active")
def set_active(user_id: UUID, active: bool = True, db: Session = Depends(get_db), admin: User = Depends(require_roles(UserRole.admin))):
    u = admin_service.set_user_active(db, admin.id, user_id, active)
    return {"id": u.id, "is_active": u.is_active}


@router.get("/companies")
def companies(db: Session = Depends(get_db), admin: User = Depends(require_roles(UserRole.admin))):
    rows = list(db.scalars(select(Company)))
    return [
        {
            "id": c.id,
            "name": c.name,
            "website": c.website,
            "verification_status": c.verification_status,
            "verification_notes": c.verification_notes,
        }
        for c in rows
    ]


@router.post("/companies/{company_id}/verify")
def verify(
    company_id: UUID,
    status: CompanyVerification,
    notes: str | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.admin)),
):
    c = admin_service.verify_company(db, admin.id, company_id, status, notes)
    return {"id": c.id, "verification_status": c.verification_status}


@router.get("/jobs")
def jobs(db: Session = Depends(get_db), admin: User = Depends(require_roles(UserRole.admin))):
    rows, total = search_jobs(db, status=None, page=1, page_size=100)
    return {"items": [job_to_dict(j) for j in rows], "total": total}


@router.get("/analytics")
def analytics(db: Session = Depends(get_db), admin: User = Depends(require_roles(UserRole.admin))):
    return admin_service.analytics(db)


@router.get("/audit")
def audit(db: Session = Depends(get_db), admin: User = Depends(require_roles(UserRole.admin))):
    rows = admin_service.list_audit(db)
    return [
        {
            "id": a.id,
            "action": a.action,
            "resource_type": a.resource_type,
            "resource_id": a.resource_id,
            "details": a.details,
            "created_at": a.created_at,
            "actor_user_id": a.actor_user_id,
        }
        for a in rows
    ]


@router.post("/drives")
def create_drive(payload: DriveCreate, db: Session = Depends(get_db), admin: User = Depends(require_roles(UserRole.admin))):
    d = admin_service.create_drive(db, admin.id, payload.title, payload.description, payload.starts_at, payload.ends_at, payload.job_ids)
    return {"id": d.id, "title": d.title}


@router.get("/drives")
def list_drives(db: Session = Depends(get_db), admin: User = Depends(require_roles(UserRole.admin))):
    rows = list(db.scalars(select(PlacementDrive)))
    return [{"id": d.id, "title": d.title, "description": d.description, "is_active": d.is_active} for d in rows]


@router.get("/export/applications.csv")
def export_apps(db: Session = Depends(get_db), admin: User = Depends(require_roles(UserRole.admin))):
    from fastapi.responses import PlainTextResponse
    from app.models.entities import Application

    rows = list(db.scalars(select(Application)))
    lines = ["id,job_id,student_id,status,submitted_at"]
    for a in rows:
        lines.append(f"{a.id},{a.job_id},{a.student_id},{a.status.value},{a.submitted_at.isoformat()}")
    return PlainTextResponse("\n".join(lines), media_type="text/csv")


@router.get("/recruiter-dashboard-stats")
def recruiter_stats(db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.recruiter))):
    from sqlalchemy import func
    from app.models.entities import Application, CompanyMembership, JobPosting
    from app.services.job_service import recruiter_profile

    rec = recruiter_profile(db, user.id)
    company_ids = [m.company_id for m in db.scalars(select(CompanyMembership).where(CompanyMembership.recruiter_id == rec.id))]
    job_count = db.scalar(select(func.count()).where(JobPosting.company_id.in_(company_ids))) or 0
    app_count = db.scalar(
        select(func.count())
        .select_from(Application)
        .join(JobPosting, Application.job_id == JobPosting.id)
        .where(JobPosting.company_id.in_(company_ids))
    ) or 0
    return {"jobs": job_count, "applications": app_count, "company_ids": [str(c) for c in company_ids]}
