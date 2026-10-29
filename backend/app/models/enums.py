import enum


class UserRole(str, enum.Enum):
    student = "student"
    recruiter = "recruiter"
    admin = "admin"


class CompanyVerification(str, enum.Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


class MembershipRole(str, enum.Enum):
    owner = "owner"
    member = "member"


class JobStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    closed = "closed"
    archived = "archived"


class ResumeStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    processed = "processed"
    failed = "failed"
    no_text = "no_text"


class SkillSource(str, enum.Enum):
    extracted = "extracted"
    confirmed = "confirmed"
    added_by_student = "added_by_student"


class RequirementKind(str, enum.Enum):
    required = "required"
    preferred = "preferred"


class ApplicationStatus(str, enum.Enum):
    applied = "applied"
    under_review = "under_review"
    shortlisted = "shortlisted"
    interview_scheduled = "interview_scheduled"
    selected = "selected"
    rejected = "rejected"
    withdrawn = "withdrawn"


class EligibilityStatus(str, enum.Enum):
    eligible = "eligible"
    ineligible = "ineligible"
    unknown = "unknown"


class MatchingMethod(str, enum.Enum):
    semantic_weighted = "semantic_weighted"
    tfidf_weighted = "tfidf_weighted"
    skill_only = "skill_only"


class InterviewStatus(str, enum.Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
    rescheduled = "rescheduled"


class NotificationType(str, enum.Enum):
    application_status = "application_status"
    interview = "interview"
    system = "system"
    match = "match"


ALLOWED_STATUS_TRANSITIONS: dict[ApplicationStatus, set[ApplicationStatus]] = {
    ApplicationStatus.applied: {
        ApplicationStatus.under_review,
        ApplicationStatus.withdrawn,
        ApplicationStatus.rejected,
        ApplicationStatus.shortlisted,
    },
    ApplicationStatus.under_review: {
        ApplicationStatus.shortlisted,
        ApplicationStatus.rejected,
        ApplicationStatus.withdrawn,
        ApplicationStatus.interview_scheduled,
    },
    ApplicationStatus.shortlisted: {
        ApplicationStatus.interview_scheduled,
        ApplicationStatus.rejected,
        ApplicationStatus.withdrawn,
        ApplicationStatus.selected,
    },
    ApplicationStatus.interview_scheduled: {
        ApplicationStatus.selected,
        ApplicationStatus.rejected,
        ApplicationStatus.withdrawn,
        ApplicationStatus.interview_scheduled,
    },
    ApplicationStatus.selected: set(),
    ApplicationStatus.rejected: set(),
    ApplicationStatus.withdrawn: set(),
}
