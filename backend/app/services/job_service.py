from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.ai.matching import content_hash, normalize_skill_list
from app.models.entities import CompanyMembership, JobPosting, JobRequirement, RecruiterProfile
from app.models.enums import JobStatus, MembershipRole, RequirementKind
from app.schemas.domain import JobCreate, JobUpdate
from app.services.audit import audit
from app.services.errors import Forbidden, NotFound


def recruiter_profile(db: Session, user_id: UUID) -> RecruiterProfile:
    rec = db.scalar(select(RecruiterProfile).where(RecruiterProfile.user_id == user_id))
    if not rec:
        raise NotFound("Recruiter profile not found")
    return rec


def memberships_for(db: Session, recruiter_id: UUID) -> list[CompanyMembership]:
    return list(db.scalars(select(CompanyMembership).where(CompanyMembership.recruiter_id == recruiter_id)))


def assert_company_access(db: Session, recruiter: RecruiterProfile, company_id: UUID) -> CompanyMembership:
    mem = db.scalar(
        select(CompanyMembership).where(
            CompanyMembership.recruiter_id == recruiter.id,
            CompanyMembership.company_id == company_id,
        )
    )
    if not mem:
        raise Forbidden("You cannot manage this company")
    return mem


def _set_requirements(job: JobPosting, required: list[str], preferred: list[str]) -> None:
    job.requirements.clear()
    for skill in normalize_skill_list(required):
        job.requirements.append(
            JobRequirement(
                skill_slug=skill["slug"], skill_name=skill["name"], kind=RequirementKind.required
            )
        )
    for skill in normalize_skill_list(preferred):
        job.requirements.append(
            JobRequirement(
                skill_slug=skill["slug"], skill_name=skill["name"], kind=RequirementKind.preferred
            )
        )


def create_job(db: Session, user_id: UUID, payload: JobCreate) -> JobPosting:
    rec = recruiter_profile(db, user_id)
    mems = memberships_for(db, rec.id)
    if not mems:
        raise Forbidden("You are not a member of any company")
    company_id = payload.company_id or mems[0].company_id
    assert_company_access(db, rec, company_id)
    job = JobPosting(
        company_id=company_id,
        created_by_recruiter_id=rec.id,
        title=payload.title,
        description=payload.description,
        responsibilities=payload.responsibilities,
        location=payload.location,
        employment_type=payload.employment_type,
        min_cgpa=payload.min_cgpa,
        min_graduation_year=payload.min_graduation_year,
        max_graduation_year=payload.max_graduation_year,
        min_experience_years=payload.min_experience_years,
        education_requirement=payload.education_requirement,
        application_deadline=payload.application_deadline,
        status=JobStatus.draft,
        content_hash=content_hash(payload.title, payload.description, payload.responsibilities or ""),
    )
    db.add(job)
    db.flush()
    _set_requirements(job, payload.required_skills, payload.preferred_skills)
    audit(db, user_id, "job_create", "job", str(job.id))
    db.commit()
    db.refresh(job)
    return job


def update_job(db: Session, user_id: UUID, job_id: UUID, payload: JobUpdate) -> JobPosting:
    rec = recruiter_profile(db, user_id)
    job = db.scalar(select(JobPosting).options(selectinload(JobPosting.requirements)).where(JobPosting.id == job_id))
    if not job:
        raise NotFound("Job not found")
    assert_company_access(db, rec, job.company_id)
    data = payload.model_dump(exclude_unset=True)
    req = data.pop("required_skills", None)
    pref = data.pop("preferred_skills", None)
    for k, v in data.items():
        setattr(job, k, v)
    if req is not None or pref is not None:
        current_req = [r.skill_name for r in job.requirements if r.kind == RequirementKind.required]
        current_pref = [r.skill_name for r in job.requirements if r.kind == RequirementKind.preferred]
        _set_requirements(job, req if req is not None else current_req, pref if pref is not None else current_pref)
    job.content_hash = content_hash(job.title, job.description, job.responsibilities or "")
    job.embedding = None
    audit(db, user_id, "job_update", "job", str(job.id))
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: UUID) -> JobPosting:
    job = db.scalar(select(JobPosting).options(selectinload(JobPosting.requirements), selectinload(JobPosting.company)).where(JobPosting.id == job_id))
    if not job:
        raise NotFound("Job not found")
    return job


def search_jobs(
    db: Session,
    *,
    q: str | None = None,
    status: JobStatus | None = JobStatus.published,
    page: int = 1,
    page_size: int = 20,
    company_id: UUID | None = None,
) -> tuple[list[JobPosting], int]:
    stmt = select(JobPosting).options(selectinload(JobPosting.requirements), selectinload(JobPosting.company))
    if status:
        stmt = stmt.where(JobPosting.status == status)
    if company_id:
        stmt = stmt.where(JobPosting.company_id == company_id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(JobPosting.title.ilike(like), JobPosting.description.ilike(like)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = list(
        db.scalars(stmt.order_by(JobPosting.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    )
    return rows, total


def job_to_dict(job: JobPosting) -> dict:
    req = [r.skill_name for r in job.requirements if r.kind == RequirementKind.required]
    pref = [r.skill_name for r in job.requirements if r.kind == RequirementKind.preferred]
    return {
        "id": job.id,
        "company_id": job.company_id,
        "company_name": job.company.name if job.company else "",
        "title": job.title,
        "description": job.description,
        "responsibilities": job.responsibilities,
        "location": job.location,
        "employment_type": job.employment_type,
        "min_cgpa": job.min_cgpa,
        "min_graduation_year": job.min_graduation_year,
        "max_graduation_year": job.max_graduation_year,
        "min_experience_years": job.min_experience_years,
        "education_requirement": job.education_requirement,
        "application_deadline": job.application_deadline,
        "status": job.status,
        "required_skills": req,
        "preferred_skills": pref,
        "created_at": job.created_at,
    }
