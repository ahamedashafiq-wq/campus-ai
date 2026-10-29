from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.ai.embeddings import encode_text, embedding_status
from app.ai.matching import MatchInput, compute_match, content_hash, skill_gap_report
from app.config import get_settings
from app.models.entities import JobMatch, JobPosting, Resume, StudentProfile, StudentSkill
from app.models.enums import EligibilityStatus, JobStatus, MatchingMethod, RequirementKind, SkillSource
from app.services.errors import NotFound
from app.services.job_service import get_job


def _student_text(student: StudentProfile, resume: Resume | None) -> str:
    parts = [
        student.headline or "",
        student.bio or "",
        student.experience_summary or "",
        " ".join(p.title + " " + (p.description or "") for p in student.projects),
        " ".join(s.skill_name for s in student.skills),
    ]
    if resume and resume.extraction:
        parts.append(resume.extraction.raw_text or "")
    return "\n".join(p for p in parts if p)


def _confirmed_or_extracted_skills(student: StudentProfile) -> list[str]:
    confirmed = [s.skill_name for s in student.skills if s.confirmed]
    if confirmed:
        return confirmed
    return [s.skill_name for s in student.skills]


def match_student_to_job(db: Session, student: StudentProfile, job: JobPosting) -> dict:
    resume = next((r for r in student.resumes if r.is_active), None)
    student_text = _student_text(student, resume)
    job_text = f"{job.title}\n{job.description}\n{job.responsibilities or ''}"
    req = [r.skill_slug for r in job.requirements if r.kind == RequirementKind.required]
    pref = [r.skill_slug for r in job.requirements if r.kind == RequirementKind.preferred]
    have = [s.skill_slug for s in student.skills if s.confirmed] or [s.skill_slug for s in student.skills]
    settings = get_settings()
    student_emb = None
    job_emb = job.embedding
    st_hash = content_hash(student_text)
    if resume and resume.extraction and resume.extraction.embedding and resume.extraction.content_hash == st_hash:
        student_emb = resume.extraction.embedding
    if job.embedding and job.content_hash:
        job_emb = job.embedding
    if embedding_status()["status"] == "uninitialized":
        # Do not download during request if lazy; attempt once if already importable.
        pass
    if embedding_status()["status"] == "ready" or settings.embedding_enabled:
        if student_emb is None and embedding_status()["status"] in {"ready", "uninitialized"}:
            student_emb = encode_text(student_text)
            if resume and resume.extraction and student_emb:
                resume.extraction.embedding = student_emb
        if job_emb is None:
            job_emb = encode_text(job_text)
            if job_emb:
                job.embedding = job_emb
    result = compute_match(
        MatchInput(
            student_skills=have,
            required_skills=req,
            preferred_skills=pref,
            student_text=student_text,
            job_text=job_text,
            projects=[p.title for p in student.projects],
            graduation_year=student.graduation_year,
            cgpa=student.cgpa,
            min_graduation_year=job.min_graduation_year,
            max_graduation_year=job.max_graduation_year,
            min_cgpa=job.min_cgpa,
            student_embedding=student_emb,
            job_embedding=job_emb,
            weights={
                "required": settings.match_weight_required,
                "preferred": settings.match_weight_preferred,
                "semantic": settings.match_weight_semantic,
                "evidence": settings.match_weight_evidence,
            },
        )
    )
    existing = db.scalar(select(JobMatch).where(JobMatch.job_id == job.id, JobMatch.student_id == student.id))
    payload = dict(
        overall_score=result["overall_score"],
        required_coverage=result["required_coverage"],
        preferred_coverage=result["preferred_coverage"],
        semantic_score=result["semantic_score"],
        evidence_score=result["evidence_score"],
        matching_method=MatchingMethod(result["matching_method"]),
        eligibility=EligibilityStatus(result["eligibility"]),
        explanation=result,
        student_content_hash=st_hash,
        job_content_hash=job.content_hash,
        resume_id=resume.id if resume else None,
    )
    if existing:
        for k, v in payload.items():
            setattr(existing, k, v)
        match_row = existing
    else:
        match_row = JobMatch(job_id=job.id, student_id=student.id, **payload)
        db.add(match_row)
    db.commit()
    result["match_id"] = str(match_row.id)
    result["gap"] = skill_gap_report(result)
    return result


def recommend_jobs_for_student(db: Session, user_id: UUID, limit: int = 20) -> list[dict]:
    student = db.scalar(
        select(StudentProfile)
        .options(
            selectinload(StudentProfile.skills),
            selectinload(StudentProfile.projects),
            selectinload(StudentProfile.resumes).selectinload(Resume.extraction),
        )
        .where(StudentProfile.user_id == user_id)
    )
    if not student:
        raise NotFound("Student profile not found")
    jobs = list(
        db.scalars(
            select(JobPosting)
            .options(selectinload(JobPosting.requirements), selectinload(JobPosting.company))
            .where(JobPosting.status == JobStatus.published)
            .limit(50)
        )
    )
    ranked = []
    for job in jobs:
        result = match_student_to_job(db, student, job)
        ranked.append({"job": job, "match": result})
    ranked.sort(key=lambda x: x["match"]["overall_score"], reverse=True)
    return ranked[:limit]


def match_for_ids(db: Session, student_id: UUID, job_id: UUID) -> dict:
    student = db.scalar(
        select(StudentProfile)
        .options(
            selectinload(StudentProfile.skills),
            selectinload(StudentProfile.projects),
            selectinload(StudentProfile.resumes).selectinload(Resume.extraction),
        )
        .where(StudentProfile.id == student_id)
    )
    if not student:
        raise NotFound("Student not found")
    job = get_job(db, job_id)
    return match_student_to_job(db, student, job)
