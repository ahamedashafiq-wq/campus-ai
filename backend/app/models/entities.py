from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.session import Base
from app.models.enums import (
    ApplicationStatus,
    CompanyVerification,
    EligibilityStatus,
    InterviewStatus,
    JobStatus,
    MatchingMethod,
    MembershipRole,
    NotificationType,
    RequirementKind,
    ResumeStatus,
    SkillSource,
    UserRole,
)

JSONType = JSON().with_variant(JSONB, "postgresql")


def uuid_pk() -> mapped_column:
    return mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)

    student_profile: Mapped[Optional["StudentProfile"]] = relationship(back_populates="user")
    recruiter_profile: Mapped[Optional["RecruiterProfile"]] = relationship(back_populates="user")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user")


class StudentProfile(Base, TimestampMixin):
    __tablename__ = "student_profiles"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    department: Mapped[Optional[str]] = mapped_column(String(120))
    degree: Mapped[Optional[str]] = mapped_column(String(120))
    graduation_year: Mapped[Optional[int]] = mapped_column(Integer)
    cgpa: Mapped[Optional[float]] = mapped_column(Float)
    headline: Mapped[Optional[str]] = mapped_column(String(240))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    github_url: Mapped[Optional[str]] = mapped_column(String(300))
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(300))
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(300))
    experience_summary: Mapped[Optional[str]] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="student_profile")
    resumes: Mapped[list["Resume"]] = relationship(back_populates="student")
    skills: Mapped[list["StudentSkill"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    projects: Mapped[list["StudentProject"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    applications: Mapped[list["Application"]] = relationship(back_populates="student")
    saved_jobs: Mapped[list["SavedJob"]] = relationship(back_populates="student")


class RecruiterProfile(Base, TimestampMixin):
    __tablename__ = "recruiter_profiles"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    title: Mapped[Optional[str]] = mapped_column(String(120))
    phone: Mapped[Optional[str]] = mapped_column(String(40))

    user: Mapped[User] = relationship(back_populates="recruiter_profile")
    memberships: Mapped[list["CompanyMembership"]] = relationship(back_populates="recruiter")


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    website: Mapped[Optional[str]] = mapped_column(String(300))
    description: Mapped[Optional[str]] = mapped_column(Text)
    industry: Mapped[Optional[str]] = mapped_column(String(120))
    verification_status: Mapped[CompanyVerification] = mapped_column(
        Enum(CompanyVerification, name="company_verification"),
        default=CompanyVerification.pending,
        nullable=False,
    )
    verification_notes: Mapped[Optional[str]] = mapped_column(Text)

    memberships: Mapped[list["CompanyMembership"]] = relationship(back_populates="company")
    jobs: Mapped[list["JobPosting"]] = relationship(back_populates="company")


class CompanyMembership(Base, TimestampMixin):
    __tablename__ = "company_memberships"
    __table_args__ = (UniqueConstraint("company_id", "recruiter_id", name="uq_company_recruiter"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id", ondelete="CASCADE"))
    recruiter_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("recruiter_profiles.id", ondelete="CASCADE"))
    role: Mapped[MembershipRole] = mapped_column(
        Enum(MembershipRole, name="membership_role"), default=MembershipRole.member, nullable=False
    )

    company: Mapped[Company] = relationship(back_populates="memberships")
    recruiter: Mapped[RecruiterProfile] = relationship(back_populates="memberships")


class Skill(Base, TimestampMixin):
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = uuid_pk()
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    aliases: Mapped[list] = mapped_column(JSONType, default=list)


class Resume(Base, TimestampMixin):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = uuid_pk()
    student_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_key: Mapped[str] = mapped_column(String(400), nullable=False, unique=True)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[ResumeStatus] = mapped_column(
        Enum(ResumeStatus, name="resume_status"), default=ResumeStatus.uploaded, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    student: Mapped[StudentProfile] = relationship(back_populates="resumes")
    extraction: Mapped[Optional["ResumeExtraction"]] = relationship(back_populates="resume", uselist=False)


class ResumeExtraction(Base, TimestampMixin):
    __tablename__ = "resume_extractions"

    id: Mapped[uuid.UUID] = uuid_pk()
    resume_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("resumes.id", ondelete="CASCADE"), unique=True)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    extracted_skills: Mapped[list] = mapped_column(JSONType, default=list)
    education: Mapped[list] = mapped_column(JSONType, default=list)
    experience: Mapped[list] = mapped_column(JSONType, default=list)
    projects: Mapped[list] = mapped_column(JSONType, default=list)
    certifications: Mapped[list] = mapped_column(JSONType, default=list)
    links: Mapped[dict] = mapped_column(JSONType, default=dict)
    completeness: Mapped[dict] = mapped_column(JSONType, default=dict)
    content_hash: Mapped[str] = mapped_column(String(64), default="")
    embedding: Mapped[Optional[list]] = mapped_column(JSONType)
    extraction_notes: Mapped[Optional[str]] = mapped_column(Text)
    uncertain_fields: Mapped[list] = mapped_column(JSONType, default=list)

    resume: Mapped[Resume] = relationship(back_populates="extraction")


class StudentSkill(Base, TimestampMixin):
    __tablename__ = "student_skills"
    __table_args__ = (UniqueConstraint("student_id", "skill_slug", name="uq_student_skill"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    student_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True)
    skill_slug: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    skill_name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    source: Mapped[SkillSource] = mapped_column(Enum(SkillSource, name="skill_source"), nullable=False)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    evidence: Mapped[Optional[str]] = mapped_column(Text)

    student: Mapped[StudentProfile] = relationship(back_populates="skills")


class StudentProject(Base, TimestampMixin):
    __tablename__ = "student_projects"

    id: Mapped[uuid.UUID] = uuid_pk()
    student_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    technologies: Mapped[list] = mapped_column(JSONType, default=list)
    url: Mapped[Optional[str]] = mapped_column(String(300))
    source: Mapped[str] = mapped_column(String(40), default="student")

    student: Mapped[StudentProfile] = relationship(back_populates="projects")


class JobPosting(Base, TimestampMixin):
    __tablename__ = "job_postings"

    id: Mapped[uuid.UUID] = uuid_pk()
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    created_by_recruiter_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("recruiter_profiles.id"))
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    responsibilities: Mapped[Optional[str]] = mapped_column(Text)
    location: Mapped[Optional[str]] = mapped_column(String(160))
    employment_type: Mapped[Optional[str]] = mapped_column(String(80))
    min_cgpa: Mapped[Optional[float]] = mapped_column(Float)
    min_graduation_year: Mapped[Optional[int]] = mapped_column(Integer)
    max_graduation_year: Mapped[Optional[int]] = mapped_column(Integer)
    min_experience_years: Mapped[Optional[float]] = mapped_column(Float)
    education_requirement: Mapped[Optional[str]] = mapped_column(String(200))
    application_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"), default=JobStatus.draft, nullable=False, index=True
    )
    content_hash: Mapped[str] = mapped_column(String(64), default="")
    embedding: Mapped[Optional[list]] = mapped_column(JSONType)

    company: Mapped[Company] = relationship(back_populates="jobs")
    requirements: Mapped[list["JobRequirement"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    applications: Mapped[list["Application"]] = relationship(back_populates="job")
    matches: Mapped[list["JobMatch"]] = relationship(back_populates="job")


class JobRequirement(Base, TimestampMixin):
    __tablename__ = "job_requirements"

    id: Mapped[uuid.UUID] = uuid_pk()
    job_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("job_postings.id", ondelete="CASCADE"), index=True)
    skill_slug: Mapped[str] = mapped_column(String(120), nullable=False)
    skill_name: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[RequirementKind] = mapped_column(Enum(RequirementKind, name="requirement_kind"), nullable=False)

    job: Mapped[JobPosting] = relationship(back_populates="requirements")


class JobMatch(Base, TimestampMixin):
    __tablename__ = "job_matches"
    __table_args__ = (UniqueConstraint("job_id", "student_id", name="uq_job_student_match"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    job_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("job_postings.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True)
    resume_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("resumes.id", ondelete="SET NULL"))
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    required_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    preferred_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    semantic_score: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    matching_method: Mapped[MatchingMethod] = mapped_column(
        Enum(MatchingMethod, name="matching_method"), nullable=False
    )
    eligibility: Mapped[EligibilityStatus] = mapped_column(
        Enum(EligibilityStatus, name="eligibility_status"), nullable=False
    )
    explanation: Mapped[dict] = mapped_column(JSONType, default=dict)
    student_content_hash: Mapped[str] = mapped_column(String(64), default="")
    job_content_hash: Mapped[str] = mapped_column(String(64), default="")

    job: Mapped[JobPosting] = relationship(back_populates="matches")


class Application(Base, TimestampMixin):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("job_id", "student_id", name="uq_job_student_application"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    job_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("job_postings.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True)
    resume_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("resumes.id", ondelete="SET NULL"))
    cover_note: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status"),
        default=ApplicationStatus.applied,
        nullable=False,
        index=True,
    )
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped[JobPosting] = relationship(back_populates="applications")
    student: Mapped[StudentProfile] = relationship(back_populates="applications")
    history: Mapped[list["ApplicationStatusHistory"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    interviews: Mapped[list["Interview"]] = relationship(back_populates="application")


class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"

    id: Mapped[uuid.UUID] = uuid_pk()
    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    from_status: Mapped[Optional[ApplicationStatus]] = mapped_column(
        Enum(ApplicationStatus, name="application_status"), nullable=True
    )
    to_status: Mapped[ApplicationStatus] = mapped_column(Enum(ApplicationStatus, name="application_status"), nullable=False)
    changed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("users.id"))
    note: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped[Application] = relationship(back_populates="history")


class SavedJob(Base, TimestampMixin):
    __tablename__ = "saved_jobs"
    __table_args__ = (UniqueConstraint("job_id", "student_id", name="uq_saved_job"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    job_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("job_postings.id", ondelete="CASCADE"))
    student_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True)

    student: Mapped[StudentProfile] = relationship(back_populates="saved_jobs")


class Interview(Base, TimestampMixin):
    __tablename__ = "interviews"

    id: Mapped[uuid.UUID] = uuid_pk()
    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location_or_link: Mapped[Optional[str]] = mapped_column(String(400))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[InterviewStatus] = mapped_column(
        Enum(InterviewStatus, name="interview_status"), default=InterviewStatus.scheduled, nullable=False
    )

    application: Mapped[Application] = relationship(back_populates="interviews")


class PlacementDrive(Base, TimestampMixin):
    __tablename__ = "placement_drives"

    id: Mapped[uuid.UUID] = uuid_pk()
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    jobs: Mapped[list["PlacementDriveJob"]] = relationship(back_populates="drive", cascade="all, delete-orphan")


class PlacementDriveJob(Base, TimestampMixin):
    __tablename__ = "placement_drive_jobs"
    __table_args__ = (UniqueConstraint("drive_id", "job_id", name="uq_drive_job"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    drive_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("placement_drives.id", ondelete="CASCADE"))
    job_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("job_postings.id", ondelete="CASCADE"))

    drive: Mapped[PlacementDrive] = relationship(back_populates="jobs")


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType, name="notification_type"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    data: Mapped[dict] = mapped_column(JSONType, default=dict)

    user: Mapped[User] = relationship(back_populates="notifications")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = uuid_pk()
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(80))
    details: Mapped[dict] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
