from fastapi import APIRouter

from app.api.v1.routes import admin, applications, auth, health, interviews, jobs, matching, notifications, recruiters, resumes, students

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(students.router)
api_router.include_router(resumes.router)
api_router.include_router(jobs.router)
api_router.include_router(matching.router)
api_router.include_router(applications.router)
api_router.include_router(interviews.router)
api_router.include_router(notifications.router)
api_router.include_router(recruiters.router)
api_router.include_router(admin.router)
