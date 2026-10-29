from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.entities import SavedJob, StudentProfile, StudentProject, StudentSkill, User
from app.models.enums import UserRole
from app.schemas.domain import ProjectIn, SkillIn, StudentProfileOut, StudentProfileUpdate, StudentSkillOut
from app.services.errors import NotFound
from app.services.resume_service import confirm_skills

router = APIRouter(prefix="/students", tags=["students"])


def _profile_out(p: StudentProfile) -> StudentProfileOut:
    return StudentProfileOut(
        id=p.id,
        user_id=p.user_id,
        full_name=p.user.full_name,
        email=p.user.email,
        department=p.department,
        degree=p.degree,
        graduation_year=p.graduation_year,
        cgpa=p.cgpa,
        headline=p.headline,
        bio=p.bio,
        github_url=p.github_url,
        linkedin_url=p.linkedin_url,
        portfolio_url=p.portfolio_url,
        experience_summary=p.experience_summary,
    )


@router.get("/me", response_model=StudentProfileOut)
def get_me(db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.student, UserRole.admin))):
    p = db.scalar(select(StudentProfile).options(selectinload(StudentProfile.user)).where(StudentProfile.user_id == user.id))
    if not p:
        raise NotFound("Student profile not found")
    return _profile_out(p)


@router.patch("/me", response_model=StudentProfileOut)
def update_me(payload: StudentProfileUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.student))):
    p = db.scalar(select(StudentProfile).options(selectinload(StudentProfile.user)).where(StudentProfile.user_id == user.id))
    if not p:
        raise NotFound("Student profile not found")
    data = payload.model_dump(exclude_unset=True)
    if "full_name" in data:
        p.user.full_name = data.pop("full_name")
    for k, v in data.items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return _profile_out(p)


@router.get("/me/skills", response_model=list[StudentSkillOut])
def my_skills(db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.student))):
    p = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
    if not p:
        raise NotFound("Student profile not found")
    return list(db.scalars(select(StudentSkill).where(StudentSkill.student_id == p.id)))


@router.post("/me/skills", response_model=list[StudentSkillOut])
def set_skills(payload: list[SkillIn], db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.student))):
    names = [s.name for s in payload]
    return confirm_skills(db, user.id, names, confirmed=True)


@router.get("/me/projects")
def my_projects(db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.student))):
    p = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
    if not p:
        raise NotFound("Student profile not found")
    rows = list(db.scalars(select(StudentProject).where(StudentProject.student_id == p.id)))
    return [
        {"id": r.id, "title": r.title, "description": r.description, "technologies": r.technologies, "url": r.url, "source": r.source}
        for r in rows
    ]


@router.post("/me/projects")
def add_project(payload: ProjectIn, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.student))):
    p = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
    if not p:
        raise NotFound("Student profile not found")
    row = StudentProject(
        student_id=p.id,
        title=payload.title,
        description=payload.description,
        technologies=payload.technologies,
        url=payload.url,
        source="student",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "title": row.title}


@router.post("/me/saved-jobs/{job_id}")
def save_job(job_id, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.student))):
    p = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
    existing = db.scalar(select(SavedJob).where(SavedJob.student_id == p.id, SavedJob.job_id == job_id))
    if existing:
        return {"saved": True}
    db.add(SavedJob(student_id=p.id, job_id=job_id))
    db.commit()
    return {"saved": True}


@router.delete("/me/saved-jobs/{job_id}")
def unsave_job(job_id, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.student))):
    p = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
    row = db.scalar(select(SavedJob).where(SavedJob.student_id == p.id, SavedJob.job_id == job_id))
    if row:
        db.delete(row)
        db.commit()
    return {"saved": False}


@router.get("/me/saved-jobs")
def list_saved(db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.student))):
    from app.models.entities import JobPosting
    from app.services.job_service import job_to_dict

    p = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
    rows = list(db.scalars(select(SavedJob).where(SavedJob.student_id == p.id)))
    out = []
    for r in rows:
        job = db.scalar(select(JobPosting).options(selectinload(JobPosting.requirements), selectinload(JobPosting.company)).where(JobPosting.id == r.job_id))
        out.append({"job_id": r.job_id, "job": job_to_dict(job) if job else None})
    return out


@router.get("/me/dashboard")
def student_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.student)),
):
    from app.models.entities import Application, Interview, Resume
    from app.models.enums import InterviewStatus
    from app.services.match_service import recommend_jobs_for_student
    from app.services.job_service import job_to_dict

    p = db.scalar(
        select(StudentProfile)
        .options(
            selectinload(StudentProfile.user),
            selectinload(StudentProfile.skills),
            selectinload(StudentProfile.resumes).selectinload(Resume.extraction),
        )
        .where(StudentProfile.user_id == user.id)
    )
    if not p:
        raise NotFound("Student profile not found")
    recs = recommend_jobs_for_student(db, user.id, limit=8)
    apps = list(db.scalars(select(Application).where(Application.student_id == p.id)))
    interviews = list(
        db.scalars(
            select(Interview)
            .join(Application, Interview.application_id == Application.id)
            .where(Application.student_id == p.id, Interview.status == InterviewStatus.scheduled)
        )
    )
    active_resume = next((r for r in p.resumes if r.is_active), None)
    completeness = {}
    if active_resume and active_resume.extraction:
        completeness = active_resume.extraction.completeness or {}
    status_counts: dict[str, int] = {}
    for a in apps:
        key = a.status.value
        status_counts[key] = status_counts.get(key, 0) + 1
    return {
        "profile": _profile_out(p),
        "skills": [{"name": s.skill_name, "confirmed": s.confirmed, "source": s.source.value} for s in p.skills],
        "resume": {
            "id": str(active_resume.id) if active_resume else None,
            "status": active_resume.status.value if active_resume else None,
            "completeness": completeness,
            "error_message": active_resume.error_message if active_resume else None,
        },
        "recommendations": [
            {"job": job_to_dict(item["job"]), "match": item["match"]} for item in recs
        ],
        "applications_count": len(apps),
        "upcoming_interviews": [
            {"id": i.id, "scheduled_at": i.scheduled_at, "location_or_link": i.location_or_link} for i in interviews
        ],
        "application_status_counts": status_counts,
    }
