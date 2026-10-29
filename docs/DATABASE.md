# Database

PostgreSQL is the production database. SQLAlchemy 2 maps tables in `backend/app/models/entities.py`. Alembic revision `0001` creates the schema with `Base.metadata.create_all`.

## Initialize

```powershell
cd backend
alembic upgrade head
```

Do not drop an existing production database. `alembic downgrade` is destructive and must not be used against live data.

## Principal tables

- `users` — credentials, role, activity
- `student_profiles`, `recruiter_profiles`
- `companies`, `company_memberships`
- `resumes`, `resume_extractions`
- `skills`, `student_skills`, `student_projects`
- `job_postings`, `job_requirements`, `job_matches`
- `applications`, `application_status_history`
- `saved_jobs`, `interviews`
- `placement_drives`, `placement_drive_jobs`
- `notifications`, `audit_logs`
- `password_reset_tokens`, `email_verification_tokens`

## Rules

- Unique `(job_id, student_id)` on applications and matches
- Company membership uniqueness
- Foreign keys with cascade on owned child rows
- Timestamps on mutable records
- Application status history is append-only in normal use

Tests may use SQLite in memory. That is a test fixture, not the production datastore.
