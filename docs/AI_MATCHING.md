# AI matching

The matching engine lives in `backend/app/ai/matching.py`. API routes do not implement scoring.

## Components (0–100, then weighted)

| Component | Default weight | Source |
| --- | --- | --- |
| Required-skill coverage | 40% | Confirmed student skills vs job required skills |
| Preferred-skill coverage | 15% | Confirmed student skills vs job preferred skills |
| Semantic similarity | 25% | Sentence embedding cosine similarity, else TF-IDF |
| Project/experience evidence | 20% | Resume and project text mentions of those skills |

If semantic similarity cannot be computed, its weight is redistributed across the other components. The response `matching_method` identifies `semantic_weighted`, `tfidf_weighted`, or `skill_only`.

These weights are engineering heuristics. They are not validated predictors of hiring or placement.

## Model

Default: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, general English paraphrase model). Limitations: short context, not domain-tuned for CVs, weaker on non-English text, not a ranking model for employability.

Load once per worker via `backend/app/ai/embeddings.py`. Startup does not block on a download. `EMBEDDING_LAZY_LOAD=true` is the default. For offline environments, download the model once and set `EMBEDDING_MODEL_PATH`.

Install extras with `pip install -r backend/requirements-ai.txt`.

## Eligibility

Graduation year and CGPA requirements are evaluated separately. Missing student data yields `unknown`, not `ineligible`. Missing required skills are explained; they do not auto-reject.

## Skill extraction

`skill_taxonomy.json` is a maintained dictionary with aliases. Extraction never invents skills. Students can confirm or add skills; source and confirmation stay distinguishable.

## OCR and LLM

OCR is off unless `OCR_ENABLED` is implemented in the environment. Scanned PDFs currently return `no_text` with a clear message.

Optional LLM advice cannot override deterministic skill comparison. Without credentials, the LLM interface returns `enabled: false`.
