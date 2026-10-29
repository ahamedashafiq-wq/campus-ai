from typing import Optional
from uuid import UUID

from fastapi import Cookie, Depends, Header, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import get_db
from app.models.entities import User
from app.models.enums import UserRole
from app.security.auth import decode_access_token
from app.services.errors import Forbidden, Unauthorized


def _csrf_required(request: Request) -> bool:
    return request.method in {"POST", "PUT", "PATCH", "DELETE"}


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(default=None, alias=None),
    authorization: Optional[str] = Header(default=None),
    x_csrf_token: Optional[str] = Header(default=None, alias="X-CSRF-Token"),
) -> User:
    settings = get_settings()
    token = None
    cookie_token = request.cookies.get(settings.auth_cookie_name)
    if cookie_token:
        token = cookie_token
        if _csrf_required(request):
            csrf_cookie = request.cookies.get(settings.csrf_cookie_name)
            if not csrf_cookie or not x_csrf_token or csrf_cookie != x_csrf_token:
                raise Unauthorized("CSRF token missing or invalid")
    elif authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    if not token:
        raise Unauthorized("Authentication required")
    try:
        payload = decode_access_token(token)
        user_id = UUID(payload["sub"])
    except Exception as exc:
        raise Unauthorized("Invalid or expired session") from exc
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise Unauthorized("Invalid or expired session")
    return user


def require_roles(*roles: UserRole):
    def _inner(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise Forbidden("You do not have permission to perform this action")
        return user

    return _inner


def optional_user(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    settings = get_settings()
    token = request.cookies.get(settings.auth_cookie_name)
    if not token:
        auth = request.headers.get("authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1]
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        return db.get(User, UUID(payload["sub"]))
    except Exception:
        return None
