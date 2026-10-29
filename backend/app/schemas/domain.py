from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.enums import (
    ApplicationStatus,
    CompanyVerification,
    InterviewStatus,
    JobStatus,
    ResumeStatus,
    SkillSource,
)


class StudentProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=200)
    department: Optional[str] = Field(default=None, max_length=120)
    degree: Optional[str] = Field(default=None, max_length=120)
    graduation_year: Optional[int] = Field(default=None, ge=1990, le=2100)
    cgpa: Optional[float] = Field(default=None, ge=0, le=10)
    headline: Optional[str] = Field(default=None, max_length=240)
    bio: Optional[str] = None
    github_url: Optional[str] = Field(default=None, max_length=300)
    linkedin_url: Optional[str] = Field(default=None, max_length=300)
    portfolio_url: Optional[str] = Field(default=None, max_length=300)
    experience_summary: Optional[str] = None


class StudentProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    full_name: str
    email: str
    department: Optional[str]
    degree: Optional[str]
    graduation_year: Optional[int]
    cgpa: Optional[float]
    headline: Optional[str]
    bio: Optional[str]
    github_url: Optional[str]
    linkedin_url: Optional[str]
    portfolio_url: Optional[str]
    experience_summary: Optional[str]


class SkillIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    confirmed: bool = True


class StudentSkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    skill_slug: str
    skill_name: str
    category: str
    source: SkillSource
    confirmed: bool
    evidence: Optional[str]


class ProjectIn(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: Optional[str] = None
    technologies: list[str] = Field(default_factory=list)
    url: Optional[str] = None


class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    original_filename: str
    content_type: str
    size_bytes: int
    status: ResumeStatus
    is_active: bool
    error_message: Optional[str]
    created_at: datetime
    extraction: Optional[dict[str, Any]] = None


class JobCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=20)
    responsibilities: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    min_cgpa: Optional[float] = Field(default=None, ge=0, le=10)
    min_graduation_year: Optional[int] = None
    max_graduation_year: Optional[int] = None
    min_experience_years: Optional[float] = Field(default=None, ge=0)
    education_requirement: Optional[str] = None
    application_deadline: Optional[datetime] = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    company_id: Optional[UUID] = None


class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    responsibilities: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    min_cgpa: Optional[float] = None
    min_graduation_year: Optional[int] = None
    max_graduation_year: Optional[int] = None
    min_experience_years: Optional[float] = None
    education_requirement: Optional[str] = None
    application_deadline: Optional[datetime] = None
    required_skills: Optional[list[str]] = None
    preferred_skills: Optional[list[str]] = None
    status: Optional[JobStatus] = None


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    company_id: UUID
    company_name: str
    title: str
    description: str
    responsibilities: Optional[str]
    location: Optional[str]
    employment_type: Optional[str]
    min_cgpa: Optional[float]
    min_graduation_year: Optional[int]
    max_graduation_year: Optional[int]
    min_experience_years: Optional[float]
    education_requirement: Optional[str]
    application_deadline: Optional[datetime]
    status: JobStatus
    required_skills: list[str]
    preferred_skills: list[str]
    created_at: datetime


class ApplicationCreate(BaseModel):
    job_id: UUID
    cover_note: Optional[str] = Field(default=None, max_length=4000)


class ApplicationStatusIn(BaseModel):
    status: ApplicationStatus
    note: Optional[str] = None


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    job_id: UUID
    student_id: UUID
    status: ApplicationStatus
    cover_note: Optional[str]
    submitted_at: datetime
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    student_name: Optional[str] = None
    match: Optional[dict[str, Any]] = None


class InterviewCreate(BaseModel):
    application_id: UUID
    scheduled_at: datetime
    location_or_link: Optional[str] = None
    notes: Optional[str] = None


class InterviewUpdate(BaseModel):
    scheduled_at: Optional[datetime] = None
    location_or_link: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[InterviewStatus] = None


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    website: Optional[str]
    description: Optional[str]
    industry: Optional[str]
    verification_status: CompanyVerification


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None


class DriveCreate(BaseModel):
    title: str
    description: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    job_ids: list[UUID] = Field(default_factory=list)


class BootstrapAdminIn(BaseModel):
    email: str
    password: str
    full_name: str = "Placement Administrator"
    bootstrap_secret: str
