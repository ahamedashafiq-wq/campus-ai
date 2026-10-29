from fastapi import Response

from app.config import get_settings


def set_auth_cookies(response: Response, access_token: str, csrf_token: str) -> None:
    settings = get_settings()
    secure = settings.cookie_secure or settings.is_production
    samesite = settings.cookie_samesite
    response.set_cookie(
        settings.auth_cookie_name,
        access_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )
    response.set_cookie(
        settings.csrf_cookie_name,
        csrf_token,
        httponly=False,
        secure=secure,
        samesite=samesite,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(settings.auth_cookie_name, path="/")
    response.delete_cookie(settings.csrf_cookie_name, path="/")
