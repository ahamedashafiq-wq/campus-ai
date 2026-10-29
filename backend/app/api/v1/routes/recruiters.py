from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.entities import Application, Company, CompanyMembership, JobPosting, RecruiterProfile, User
from app.models.enums import UserRole
from app.schemas.domain import CompanyUpdate
from app.services.errors import NotFound
from app.services.job_service import job_to_dict, memberships_for, recruiter_profile, search_jobs

router = APIRouter(prefix="/recruiters", tags=["recruiters"])


@router.get("/me")
def me(db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.recruiter, UserRole.admin))):
    rec = recruiter_profile(db, user.id)
    mems = memberships_for(db, rec.id)
    companies = []
    for m in mems:
        c = db.get(Company, m.company_id)
        companies.append(
            {
                "id": c.id,
                "name": c.name,
                "website": c.website,
                "description": c.description,
                "industry": c.industry,
                "verification_status": c.verification_status,
                "membership_role": m.role,
            }
        )
    return {"id": rec.id, "title": rec.title, "full_name": user.full_name, "email": user.email, "companies": companies}


@router.patch("/me/company/{company_id}")
def update_company(
    company_id,
    payload: CompanyUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.recruiter)),
):
    from app.services.job_service import assert_company_access

    rec = recruiter_profile(db, user.id)
    assert_company_access(db, rec, company_id)
    c = db.get(Company, company_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit()
    return {"id": c.id, "name": c.name}


@router.get("/me/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.recruiter))):
    rec = recruiter_profile(db, user.id)
    company_ids = [m.company_id for m in memberships_for(db, rec.id)]
    jobs, total = search_jobs(db, status=None, page=1, page_size=50, company_id=company_ids[0] if company_ids else None)
    app_count = 0
    if company_ids:
        app_count = (
            db.scalar(
                select(func.count())
                .select_from(Application)
                .join(JobPosting, Application.job_id == JobPosting.id)
                .where(JobPosting.company_id.in_(company_ids))
            )
            or 0
        )
    companies = [db.get(Company, cid) for cid in company_ids]
    counts = {}
    if company_ids:
        rows = db.execute(
            select(Application.job_id, func.count())
            .join(JobPosting, Application.job_id == JobPosting.id)
            .where(JobPosting.company_id.in_(company_ids))
            .group_by(Application.job_id)
        ).all()
        counts = {str(jid): n for jid, n in rows}
    return {
        "companies": [
            {
                "id": c.id,
                "name": c.name,
                "website": c.website,
                "description": c.description,
                "industry": c.industry,
                "verification_status": c.verification_status,
            }
            for c in companies
            if c
        ],
        "jobs": [{**job_to_dict(j), "applicant_count": counts.get(str(j.id), 0)} for j in jobs],
        "job_count": total,
        "application_count": app_count,
        "applicant_counts": counts,
    }
