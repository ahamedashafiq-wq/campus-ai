from __future__ import annotations

import hashlib
import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.extract import extract_structured
from app.ai.matching import content_hash
from app.ai.pdf import PdfExtractionError, extract_pdf_text, validate_pdf_bytes
from app.config import get_settings
from app.models.entities import Resume, ResumeExtraction, StudentProfile, StudentSkill
from app.models.enums import ResumeStatus, SkillSource
from app.services.audit import audit
from app.services.errors import AppError, Forbidden, NotFound
from app.storage import get_storage


def _student_or_404(db: Session, user_id: UUID) -> StudentProfile:
    student = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user_id))
    if not student:
        raise NotFound("Student profile not found")
    return student


def upload_resume(db: Session, user_id: UUID, filename: str, content_type: str, data: bytes) -> Resume:
    settings = get_settings()
    try:
        validate_pdf_bytes(data, settings.resume_max_bytes, filename, content_type)
    except PdfExtractionError as exc:
        raise AppError(str(exc), 400, "invalid_pdf") from exc
    student = _student_or_404(db, user_id)
    digest = hashlib.sha256(data).hexdigest()
    key = f"{student.id}/{uuid.uuid4().hex}.pdf"
    stored = get_storage().save(key, data, "application/pdf")
    if not get_storage().exists(stored):
        raise AppError("File storage did not confirm the upload", 500, "storage_failed")
    for old in student.resumes:
        old.is_active = False
    resume = Resume(
        student_id=student.id,
        original_filename=filename[:255],
        stored_key=stored,
        content_type="application/pdf",
        size_bytes=len(data),
        sha256=digest,
        status=ResumeStatus.processing,
        is_active=True,
    )
    db.add(resume)
    db.flush()
    try:
        text, meta = extract_pdf_text(data)
    except PdfExtractionError as exc:
        resume.status = ResumeStatus.failed
        resume.error_message = str(exc)
        db.commit()
        raise AppError(str(exc), 400, "pdf_unreadable") from exc
    if not text.strip():
        resume.status = ResumeStatus.no_text
        resume.error_message = (
            "No extractable text was found. If this is a scanned PDF, enable OCR or upload a text-based resume."
        )
        db.add(
            ResumeExtraction(
                resume_id=resume.id,
                raw_text="",
                char_count=0,
                extraction_notes=resume.error_message,
                completeness={"has_text": False, "score": 0},
                content_hash=content_hash(""),
            )
        )
        db.commit()
        db.refresh(resume)
        return resume
    structured = extract_structured(text)
    extraction = ResumeExtraction(
        resume_id=resume.id,
        raw_text=text[:200000],
        char_count=len(text),
        extracted_skills=structured["extracted_skills"],
        education=structured["education"],
        experience=structured["experience"],
        projects=structured["projects"],
        certifications=structured["certifications"],
        links=structured["links"],
        completeness=structured["completeness"],
        uncertain_fields=structured["uncertain_fields"],
        content_hash=content_hash(text),
        extraction_notes=f"Extracted {len(text)} characters from {meta.get('page_count', 0)} page(s).",
    )
    db.add(extraction)
    for skill in structured["extracted_skills"]:
        existing = db.scalar(
            select(StudentSkill).where(
                StudentSkill.student_id == student.id, StudentSkill.skill_slug == skill["slug"]
            )
        )
        if existing:
            continue
        db.add(
            StudentSkill(
                student_id=student.id,
                skill_slug=skill["slug"],
                skill_name=skill["name"],
                category=skill["category"],
                source=SkillSource.extracted,
                confirmed=False,
            )
        )
    if structured["links"].get("github") and not student.github_url:
        student.github_url = structured["links"]["github"]
    if structured["links"].get("linkedin") and not student.linkedin_url:
        student.linkedin_url = structured["links"]["linkedin"]
    resume.status = ResumeStatus.processed
    audit(db, user_id, "resume_upload", "resume", str(resume.id), {"bytes": len(data)})
    db.commit()
    db.refresh(resume)
    return resume


def list_resumes(db: Session, user_id: UUID) -> list[Resume]:
    student = _student_or_404(db, user_id)
    return list(db.scalars(select(Resume).where(Resume.student_id == student.id).order_by(Resume.created_at.desc())))


def recruiter_can_access_resume(db: Session, user_id: UUID, resume: Resume) -> bool:
    from app.models.entities import Application, CompanyMembership, JobPosting, RecruiterProfile

    rec = db.scalar(select(RecruiterProfile).where(RecruiterProfile.user_id == user_id))
    if not rec:
        return False
    allowed = db.scalar(
        select(Application.id)
        .join(JobPosting, Application.job_id == JobPosting.id)
        .join(CompanyMembership, CompanyMembership.company_id == JobPosting.company_id)
        .where(Application.resume_id == resume.id, CompanyMembership.recruiter_id == rec.id)
    )
    return allowed is not None


def get_resume_for_user(db: Session, user_id: UUID, resume_id: UUID, *, admin: bool = False, recruiter: bool = False) -> Resume:
    resume = db.get(Resume, resume_id)
    if not resume:
        raise NotFound("Resume not found")
    if admin:
        return resume
    if recruiter:
        if recruiter_can_access_resume(db, user_id, resume):
            return resume
        raise Forbidden("You cannot access this resume")
    student = _student_or_404(db, user_id)
    if resume.student_id != student.id:
        raise Forbidden("You cannot access this resume")
    return resume


def delete_resume(db: Session, user_id: UUID, resume_id: UUID) -> None:
    resume = get_resume_for_user(db, user_id, resume_id)
    get_storage().delete(resume.stored_key)
    db.delete(resume)
    db.commit()


def load_resume_bytes(resume: Resume) -> bytes:
    return get_storage().load(resume.stored_key)


def confirm_skills(db: Session, user_id: UUID, names: list[str], confirmed: bool = True) -> list[StudentSkill]:
    student = _student_or_404(db, user_id)
    from app.ai.taxonomy import lookup_skill

    for name in names:
        meta = lookup_skill(name) or {"slug": name.lower().replace(" ", "-"), "name": name, "category": "unknown"}
        row = db.scalar(
            select(StudentSkill).where(StudentSkill.student_id == student.id, StudentSkill.skill_slug == meta["slug"])
        )
        if row:
            row.confirmed = confirmed
            if confirmed:
                row.source = SkillSource.confirmed
        else:
            db.add(
                StudentSkill(
                    student_id=student.id,
                    skill_slug=meta["slug"],
                    skill_name=meta["name"],
                    category=meta["category"],
                    source=SkillSource.added_by_student if confirmed else SkillSource.extracted,
                    confirmed=confirmed,
                )
            )
    db.commit()
    return list(db.scalars(select(StudentSkill).where(StudentSkill.student_id == student.id)))
