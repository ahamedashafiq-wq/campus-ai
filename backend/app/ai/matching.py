from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Iterable, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sk_cosine

from app.ai.embeddings import cosine_similarity, encode_text, embedding_status
from app.ai.taxonomy import lookup_skill
from app.models.enums import EligibilityStatus, MatchingMethod

DEFAULT_WEIGHTS = {
    "required": 0.40,
    "preferred": 0.15,
    "semantic": 0.25,
    "evidence": 0.20,
}


def content_hash(*parts: str) -> str:
    h = hashlib.sha256()
    for part in parts:
        h.update((part or "").encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()


def normalize_skill_list(values: Iterable[str]) -> list[dict]:
    out: dict[str, dict] = {}
    for raw in values:
        if not raw:
            continue
        found = lookup_skill(raw) or {
            "slug": re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-"),
            "name": raw.strip(),
            "category": "unknown",
        }
        out[found["slug"]] = {"slug": found["slug"], "name": found["name"], "category": found.get("category", "unknown")}
    return list(out.values())


def coverage_score(have: set[str], need: list[str]) -> tuple[float, list[str], list[str]]:
    if not need:
        return 100.0, [], []
    matched, missing = [], []
    have_n = {h.lower() for h in have}
    for skill in need:
        if skill.lower() in have_n:
            matched.append(skill)
        else:
            missing.append(skill)
    return round(100.0 * len(matched) / len(need), 2), matched, missing


def evidence_score(student_text: str, required: list[str], preferred: list[str], projects: list[str]) -> tuple[float, list[str]]:
    blob = (student_text + "\n" + "\n".join(projects)).lower()
    hits = []
    targets = required + preferred
    if not targets:
        return 50.0, []
    for skill in targets:
        if skill.lower() in blob:
            hits.append(skill)
    project_bonus = 10.0 if projects else 0.0
    base = 100.0 * len(hits) / max(len(targets), 1)
    return round(min(100.0, base + project_bonus), 2), hits


def tfidf_similarity(a: str, b: str) -> float:
    if not a.strip() or not b.strip():
        return 0.0
    vec = TfidfVectorizer(stop_words="english", max_features=5000)
    try:
        matrix = vec.fit_transform([a, b])
    except ValueError:
        return 0.0
    score = float(sk_cosine(matrix[0:1], matrix[1:2])[0][0])
    return max(0.0, min(1.0, score))


def semantic_or_tfidf(student_text: str, job_text: str, student_emb: Optional[list[float]], job_emb: Optional[list[float]]) -> tuple[float, MatchingMethod, str]:
    status = embedding_status()
    if status["status"] == "ready":
        if student_emb is None:
            student_emb = encode_text(student_text)
        if job_emb is None:
            job_emb = encode_text(job_text)
        if student_emb and job_emb:
            sim = cosine_similarity(student_emb, job_emb)
            return round(sim * 100.0, 2), MatchingMethod.semantic_weighted, "sentence-transformers cosine similarity"
    tfidf = tfidf_similarity(student_text, job_text)
    method = MatchingMethod.tfidf_weighted if student_text.strip() and job_text.strip() else MatchingMethod.skill_only
    note = "TF-IDF cosine similarity (semantic model unavailable or unused)"
    if method == MatchingMethod.skill_only:
        note = "Skill coverage only; insufficient text for semantic/TF-IDF similarity"
    return round(tfidf * 100.0, 2), method, note


def weighted_total(
    required: float,
    preferred: float,
    semantic: float,
    evidence: float,
    weights: Optional[dict[str, float]] = None,
    semantic_available: bool = True,
) -> float:
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)
    if not semantic_available:
        # Redistribute semantic weight across the remaining components.
        leftover = w["semantic"]
        w["semantic"] = 0.0
        denom = w["required"] + w["preferred"] + w["evidence"]
        if denom <= 0:
            return 0.0
        w["required"] += leftover * (w["required"] / denom)
        w["preferred"] += leftover * (w["preferred"] / denom)
        w["evidence"] += leftover * (w["evidence"] / denom)
    total = (
        required * w["required"]
        + preferred * w["preferred"]
        + semantic * w["semantic"]
        + evidence * w["evidence"]
    )
    return round(max(0.0, min(100.0, total)), 2)


def eligibility_from_profile(
    *,
    graduation_year: Optional[int],
    cgpa: Optional[float],
    min_grad: Optional[int],
    max_grad: Optional[int],
    min_cgpa: Optional[float],
    missing_required: list[str],
) -> tuple[EligibilityStatus, list[str]]:
    reasons = []
    unknown = False
    if min_grad is not None or max_grad is not None:
        if graduation_year is None:
            unknown = True
            reasons.append("Graduation year is not available; eligibility cannot yet be determined")
        else:
            if min_grad is not None and graduation_year < min_grad:
                reasons.append(f"Graduation year {graduation_year} is before the minimum {min_grad}")
            if max_grad is not None and graduation_year > max_grad:
                reasons.append(f"Graduation year {graduation_year} is after the maximum {max_grad}")
    if min_cgpa is not None:
        if cgpa is None:
            unknown = True
            reasons.append("CGPA is not available; eligibility cannot yet be determined")
        elif cgpa + 1e-9 < min_cgpa:
            reasons.append(f"CGPA {cgpa} is below the required {min_cgpa}")
    # Missing required skills are informational for recruiters; they do not auto-reject.
    if reasons and any("before" in r or "after" in r or "below" in r for r in reasons):
        return EligibilityStatus.ineligible, reasons
    if unknown:
        return EligibilityStatus.unknown, reasons
    return EligibilityStatus.eligible, ["Known mandatory academic requirements are met or were not specified"]


@dataclass
class MatchInput:
    student_skills: list[str]
    required_skills: list[str]
    preferred_skills: list[str]
    student_text: str
    job_text: str
    projects: list[str] = field(default_factory=list)
    graduation_year: Optional[int] = None
    cgpa: Optional[float] = None
    min_graduation_year: Optional[int] = None
    max_graduation_year: Optional[int] = None
    min_cgpa: Optional[float] = None
    student_embedding: Optional[list[float]] = None
    job_embedding: Optional[list[float]] = None
    weights: Optional[dict[str, float]] = None


def compute_match(inp: MatchInput) -> dict:
    have = {s.lower() for s in inp.student_skills}
    req_score, matched_req, missing_req = coverage_score(have, [s.lower() for s in inp.required_skills])
    pref_score, matched_pref, missing_pref = coverage_score(have, [s.lower() for s in inp.preferred_skills])
    ev_score, evidence_hits = evidence_score(inp.student_text, inp.required_skills, inp.preferred_skills, inp.projects)
    sem_score, method, sem_note = semantic_or_tfidf(
        inp.student_text, inp.job_text, inp.student_embedding, inp.job_embedding
    )
    semantic_available = method == MatchingMethod.semantic_weighted
    overall = weighted_total(
        req_score, pref_score, sem_score, ev_score, inp.weights, semantic_available=semantic_available or method == MatchingMethod.tfidf_weighted
    )
    if method == MatchingMethod.skill_only:
        overall = weighted_total(req_score, pref_score, 0.0, ev_score, inp.weights, semantic_available=False)
    elig, elig_reasons = eligibility_from_profile(
        graduation_year=inp.graduation_year,
        cgpa=inp.cgpa,
        min_grad=inp.min_graduation_year,
        max_grad=inp.max_graduation_year,
        min_cgpa=inp.min_cgpa,
        missing_required=missing_req,
    )
    weak_evidence = [s for s in matched_req + matched_pref if s not in {h.lower() for h in evidence_hits}]
    recommendations = []
    for skill in missing_req:
        recommendations.append(f"Build a project that demonstrates {skill} and add it to your confirmed skills.")
    for skill in missing_pref[:5]:
        recommendations.append(f"Consider learning {skill} to improve preferred-skill coverage.")
    if not inp.student_text.strip():
        recommendations.append("Upload a text-extractable PDF resume so semantic matching can use real resume content.")
    return {
        "overall_score": overall,
        "required_coverage": req_score,
        "preferred_coverage": pref_score,
        "semantic_score": sem_score,
        "evidence_score": ev_score,
        "matching_method": method.value,
        "semantic_note": sem_note,
        "matched_required_skills": matched_req,
        "matched_preferred_skills": matched_pref,
        "missing_required_skills": missing_req,
        "missing_preferred_skills": missing_pref,
        "relevant_resume_evidence": evidence_hits,
        "skills_needing_stronger_evidence": weak_evidence,
        "unknown_requirements": [s for s in inp.required_skills if lookup_skill(s) is None],
        "eligibility": elig.value,
        "eligibility_reasons": elig_reasons,
        "improvement_recommendations": recommendations,
        "weights_used": inp.weights or DEFAULT_WEIGHTS,
        "disclaimer": "Scores are engineering heuristics, not validated predictors of hiring or placement success. Recruiters remain responsible for hiring decisions.",
    }


def skill_gap_report(match: dict) -> dict:
    return {
        "missing_required_skills": match["missing_required_skills"],
        "missing_preferred_skills": match["missing_preferred_skills"],
        "skills_needing_stronger_project_evidence": match["skills_needing_stronger_evidence"],
        "unknown_requirements": match["unknown_requirements"],
        "learning_priorities": match["improvement_recommendations"],
        "verified_vs_advice": {
            "verified": "Skill presence is based on confirmed/extracted student skills compared to job requirements.",
            "advice": "Learning suggestions are generated from gaps. Completing a course does not guarantee placement.",
        },
    }
