# Architecture

CampusMatch AI is split into a Next.js browser application and a FastAPI service. The frontend never computes match scores and never stores applications in memory as the source of truth.

```
Browser  -->  Next.js (UI + /api/v1 proxy)  -->  FastAPI /api/v1  -->  PostgreSQL
                                                      |
                                                      +--> private file storage
                                                      +--> matching service
```

## Modules

| Area | Location |
| --- | --- |
| HTTP routes | `backend/app/api/v1/routes/` |
| Auth cookies, CSRF, RBAC | `backend/app/api/deps.py`, `backend/app/security/` |
| Domain services | `backend/app/services/` |
| Matching engine | `backend/app/ai/matching.py` |
| Embeddings | `backend/app/ai/embeddings.py` |
| PDF + skills | `backend/app/ai/pdf.py`, `backend/app/ai/extract.py`, `backend/app/ai/taxonomy.py` |
| Storage | `backend/app/storage/` |
| ORM models | `backend/app/models/entities.py` |
| UI | `frontend/src/app/` |

## Request flow

1. Browser calls same-origin `/api/v1/...`.
2. Next.js forwards cookies and CSRF headers to FastAPI.
3. FastAPI authenticates the HttpOnly session cookie, checks CSRF on mutating requests, then enforces role and ownership.
4. Services persist with SQLAlchemy sessions and commit after storage confirmation.

## Matching

`match_service` loads the student profile, active resume text, and job requirements, then calls `compute_match`. Results are stored in `job_matches` and returned with an explanation payload. Eligibility is computed separately from similarity and never auto-rejects an application.

## Optional services

- SMTP email (`EMAIL_PROVIDER=smtp`)
- Sentence Transformers (`EMBEDDING_ENABLED=true` and `requirements-ai.txt`)
- S3 storage (`STORAGE_BACKEND=s3`)
- LLM explanations (`LLM_PROVIDER` other than `none`)

If an optional service is unconfigured, the API reports that fact. It does not invent a successful send, upload, or generation.
