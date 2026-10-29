from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-characters-min")
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("COOKIE_SECURE", "false")
os.environ.setdefault("EMBEDDING_ENABLED", "false")
os.environ.setdefault("LOCAL_STORAGE_PATH", str(ROOT / "data" / "test-resumes"))
os.environ.setdefault("EMAIL_PROVIDER", "none")

from app.config import get_settings

get_settings.cache_clear()

from app.db.session import Base, get_db
from app.main import app
from app.models import entities  # noqa: F401

def _make_engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    return eng


@pytest.fixture
def db():
    engine = _make_engine()
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    engine = _make_engine()
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()

    def _get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    session.close()


def csrf_headers(client: TestClient) -> dict:
    token = client.cookies.get("csrf_token")
    return {"X-CSRF-Token": token} if token else {}
