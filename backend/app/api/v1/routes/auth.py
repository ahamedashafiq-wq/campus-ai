from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.cookies import clear_auth_cookies, set_auth_cookies
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.entities import User
from app.schemas.auth import (
    ChangePasswordIn,
    LoginIn,
    PasswordResetConfirmIn,
    PasswordResetRequestIn,
    RegisterRecruiterIn,
    RegisterStudentIn,
    UserOut,
)
from app.security.auth import create_access_token, new_csrf_token
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_out(user: User) -> UserOut:
    return UserOut.model_validate(user)


@router.post("/register/student", response_model=UserOut)
def register_student(payload: RegisterStudentIn, response: Response, db: Session = Depends(get_db)):
    user = auth_service.register_student(db, payload)
    token = create_access_token(user.id, user.role.value)
    set_auth_cookies(response, token, new_csrf_token())
    return _user_out(user)


@router.post("/register/recruiter", response_model=UserOut)
def register_recruiter(payload: RegisterRecruiterIn, response: Response, db: Session = Depends(get_db)):
    user = auth_service.register_recruiter(db, payload)
    token = create_access_token(user.id, user.role.value)
    set_auth_cookies(response, token, new_csrf_token())
    return _user_out(user)


@router.post("/login", response_model=UserOut)
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = auth_service.authenticate(db, payload.email, payload.password)
    token = create_access_token(user.id, user.role.value)
    set_auth_cookies(response, token, new_csrf_token())
    return _user_out(user)


@router.post("/logout")
def logout(response: Response, user: User = Depends(get_current_user)):
    clear_auth_cookies(response)
    return {"message": "Signed out"}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return _user_out(user)


@router.post("/password/change")
def change_password(payload: ChangePasswordIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    auth_service.change_password(db, user, payload.current_password, payload.new_password)
    return {"message": "Password updated"}


@router.post("/password/reset/request")
def reset_request(payload: PasswordResetRequestIn, db: Session = Depends(get_db)):
    return auth_service.request_password_reset(db, payload.email)


@router.post("/password/reset/confirm")
def reset_confirm(payload: PasswordResetConfirmIn, db: Session = Depends(get_db)):
    auth_service.confirm_password_reset(db, payload.token, payload.new_password)
    return {"message": "Password reset complete"}


@router.post("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    auth_service.verify_email_token(db, token)
    return {"message": "Email verified"}
