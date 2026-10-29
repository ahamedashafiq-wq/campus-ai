# CampusMatch AI

CampusMatch AI is a campus placement platform with real authentication, PostgreSQL persistence, private resume storage, PDF text extraction, dictionary-based skill extraction, explainable resume-to-job matching, and a recruitment workflow.

It is not a mockup. Production workflows read and write the database. Empty databases show empty states.

## Architecture

- Frontend: Next.js 15 App Router, TypeScript, Tailwind CSS, shadcn-style UI
- Backend: FastAPI, SQLAlchemy 2, Alembic, PostgreSQL
- Matching: skill coverage + project evidence + Sentence Transformers cosine similarity, with TF-IDF fallback
- Storage: local disk in development, S3-compatible object storage in production

See `docs/` for architecture, database, matching, security, deployment, and implementation status.

## Local start (Windows PowerShell)

1. Copy environment templates:

```powershell
Copy-Item .env.example .env
Copy-Item frontend\.env.example frontend\.env.local
```

2. Start PostgreSQL (Docker Compose database only):

```powershell
docker compose up db -d
```

If Docker is not installed, provide a PostgreSQL 16 instance and set `DATABASE_URL` in `.env`.

3. Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

Optional semantic model (downloads once, then cached):

```powershell
pip install -r requirements-ai.txt
```

4. First administrator (no public admin signup):

```powershell
cd backend
python -m app.cli bootstrap-admin --email admin@campus.edu --password "ChooseALongPassword1"
```

5. Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. API docs: `http://localhost:8000/api/docs`.

## Tests

```powershell
cd backend
$env:APP_ENV="test"
$env:SECRET_KEY="test-secret-key-32-characters-min"
$env:DATABASE_URL="sqlite://"
$env:EMBEDDING_ENABLED="false"
python -m pytest -q
```

```powershell
cd frontend
npm run typecheck
npm run build
```

## Development seed (never production)

```powershell
$env:ALLOW_DEV_SEED="true"
cd backend
python -m app.cli seed-dev
```

Seed users are labeled `[DEV]` and are not real placement activity.

## Verify major workflows

1. Register a student and a recruiter at `/register`.
2. Student: complete profile, upload a text PDF resume, confirm skills.
3. Recruiter: create a job, publish it.
4. Student: open the job, inspect the match explanation, apply.
5. Recruiter: open candidates, change status, schedule an interview.
6. Admin: sign in with the bootstrap account and confirm analytics match the database.

Public cloud deployment has not been performed from this workspace unless the deployment document says otherwise.
