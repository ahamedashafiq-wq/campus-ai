from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.entities import (
    Company,
    CompanyMembership,
    EmailVerificationToken,
    PasswordResetToken,
    RecruiterProfile,
    StudentProfile,
    User,
)
from app.models.enums import CompanyVerification, MembershipRole, UserRole
from app.schemas.auth import RegisterRecruiterIn, RegisterStudentIn
from app.security.auth import hash_password, verify_password
from app.services.audit import audit
from app.services.emailer import send_email
from app.services.errors import AppError, Conflict, NotFound, Unauthorized


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def register_student(db: Session, payload: RegisterStudentIn) -> User:
    if get_user_by_email(db, payload.email):
        raise Conflict("An account with this email already exists")
    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        role=UserRole.student,
        full_name=payload.full_name,
        email_verified=False,
    )
    db.add(user)
    db.flush()
    db.add(
        StudentProfile(
            user_id=user.id,
            department=payload.department,
            degree=payload.degree,
            graduation_year=payload.graduation_year,
        )
    )
    _issue_email_verification(db, user)
    audit(db, user.id, "register_student", "user", str(user.id))
    db.commit()
    db.refresh(user)
    return user


def register_recruiter(db: Session, payload: RegisterRecruiterIn) -> User:
    if get_user_by_email(db, payload.email):
        raise Conflict("An account with this email already exists")
    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        role=UserRole.recruiter,
        full_name=payload.full_name,
        email_verified=False,
    )
    db.add(user)
    db.flush()
    recruiter = RecruiterProfile(user_id=user.id, title=payload.title)
    db.add(recruiter)
    db.flush()
    company = Company(
        name=payload.company_name,
        website=payload.company_website,
        verification_status=CompanyVerification.pending,
    )
    db.add(company)
    db.flush()
    db.add(CompanyMembership(company_id=company.id, recruiter_id=recruiter.id, role=MembershipRole.owner))
    _issue_email_verification(db, user)
    audit(db, user.id, "register_recruiter", "user", str(user.id), {"company_id": str(company.id)})
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise Unauthorized("Invalid email or password")
    if not user.is_active:
        raise Unauthorized("This account is disabled")
    return user


def bootstrap_admin(db: Session, email: str, password: str, full_name: str) -> User:
    existing_admin = db.scalar(select(User).where(User.role == UserRole.admin))
    if existing_admin:
        raise Conflict("An administrator already exists. Use an existing admin to create more.")
    if get_user_by_email(db, email):
        raise Conflict("An account with this email already exists")
    user = User(
        email=email.lower(),
        hashed_password=hash_password(password),
        role=UserRole.admin,
        full_name=full_name,
        email_verified=True,
        is_active=True,
    )
    db.add(user)
    audit(db, None, "bootstrap_admin", "user", None, {"email": email.lower()})
    db.commit()
    db.refresh(user)
    return user


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _issue_email_verification(db: Session, user: User) -> None:
    raw = secrets.token_urlsafe(32)
    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=_hash_token(raw),
            expires_at=datetime.now(timezone.utc) + timedelta(days=2),
        )
    )
    settings = get_settings()
    send_email(
        user.email,
        "Verify your CampusMatch AI email",
        f"Verify your account: {settings.app_public_url}/verify-email?token={raw}\n\nIf you did not register, ignore this message.",
    )


def request_password_reset(db: Session, email: str) -> dict:
    user = get_user_by_email(db, email)
    # Always look successful to avoid account enumeration
    if not user:
        return {"accepted": True, "email_configured": get_settings().email_provider == "smtp"}
    raw = secrets.token_urlsafe(32)
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=_hash_token(raw),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
        )
    )
    db.commit()
    result = send_email(
        user.email,
        "Reset your CampusMatch AI password",
        f"Reset your password: {get_settings().app_public_url}/reset-password?token={raw}\nThis link expires in 2 hours.",
    )
    return {"accepted": True, "email_configured": result.get("sent", False) or get_settings().email_provider == "smtp"}


def confirm_password_reset(db: Session, token: str, new_password: str) -> None:
    token_hash = _hash_token(token)
    row = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used.is_(False),
        )
    )
    if not row or row.expires_at < datetime.now(timezone.utc):
        raise AppError("Invalid or expired reset token", 400, "invalid_token")
    user = db.get(User, row.user_id)
    if not user:
        raise NotFound("User not found")
    user.hashed_password = hash_password(new_password)
    row.used = True
    db.commit()


def verify_email_token(db: Session, token: str) -> None:
    row = db.scalar(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == _hash_token(token),
            EmailVerificationToken.used.is_(False),
        )
    )
    if not row or row.expires_at < datetime.now(timezone.utc):
        raise AppError("Invalid or expired verification token", 400, "invalid_token")
    user = db.get(User, row.user_id)
    if user:
        user.email_verified = True
    row.used = True
    db.commit()


def change_password(db: Session, user: User, current: str, new: str) -> None:
    if not verify_password(current, user.hashed_password):
        raise Unauthorized("Current password is incorrect")
    user.hashed_password = hash_password(new)
    db.commit()
