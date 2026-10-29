from __future__ import annotations

import re
from typing import Any

from app.ai.taxonomy import extract_skills_from_text


_DEGREE_RE = re.compile(
    r"\b(b\.?tech|b\.?e\.?|m\.?tech|m\.?s\.?|mca|bca|mba|bsc|msc|bachelor|master|phd)\b",
    re.I,
)
_YEAR_RE = re.compile(r"\b(20\d{2})\b")
_CGPA_RE = re.compile(r"\b(?:cgpa|gpa)\s*[:\-]?\s*([0-9]\.\d{1,2}|\d{1,2}\.\d{1,2})\b", re.I)
_CERT_RE = re.compile(r"(certified|certification|certificate)\s+([A-Za-z0-9 .+\-]{3,80})", re.I)
_GITHUB_RE = re.compile(r"https?://github\.com/[A-Za-z0-9_.\-]+/?", re.I)
_LINKEDIN_RE = re.compile(r"https?://(www\.)?linkedin\.com/in/[A-Za-z0-9_\-]+/?", re.I)


def _section(text: str, headings: list[str]) -> str:
    lower = text.lower()
    for heading in headings:
        idx = lower.find(heading)
        if idx >= 0:
            rest = text[idx:]
            next_breaks = [
                rest.lower().find(h, len(heading))
                for h in ("experience", "education", "projects", "skills", "certifications")
                if rest.lower().find(h, len(heading)) > 0
            ]
            end = min(next_breaks) if next_breaks else min(len(rest), 1500)
            return rest[:end]
    return ""


def extract_structured(text: str) -> dict[str, Any]:
    skills = extract_skills_from_text(text)
    education: list[dict] = []
    years = [int(y) for y in _YEAR_RE.findall(text)]
    degree_match = _DEGREE_RE.search(text)
    cgpa_match = _CGPA_RE.search(text)
    if degree_match or years or cgpa_match:
        education.append(
            {
                "degree": degree_match.group(0) if degree_match else None,
                "years_mentioned": years[:6],
                "cgpa": float(cgpa_match.group(1)) if cgpa_match else None,
                "confidence": "extracted",
            }
        )
    project_section = _section(text, ["projects", "project"])
    projects = []
    if project_section:
        for line in project_section.splitlines():
            line = line.strip(" -•\t")
            if 8 <= len(line) <= 180:
                projects.append({"title": line[:160], "description": None, "source": "extracted"})
            if len(projects) >= 8:
                break
    exp_section = _section(text, ["experience", "work experience", "internship"])
    experience = []
    if exp_section:
        experience.append({"summary": exp_section[:2000], "source": "extracted"})
    certs = [{"name": m.group(0).strip(), "source": "extracted"} for m in _CERT_RE.finditer(text)][:12]
    github = _GITHUB_RE.search(text)
    linkedin = _LINKEDIN_RE.search(text)
    uncertain = []
    if not skills:
        uncertain.append("skills")
    if not education:
        uncertain.append("education")
    completeness = {
        "has_text": bool(text.strip()),
        "skill_count": len(skills),
        "has_education": bool(education),
        "has_projects": bool(projects),
        "has_experience": bool(experience),
        "has_links": bool(github or linkedin),
        "score": min(
            100,
            (20 if text.strip() else 0)
            + min(30, len(skills) * 3)
            + (15 if education else 0)
            + (15 if projects else 0)
            + (10 if experience else 0)
            + (10 if github or linkedin else 0),
        ),
    }
    return {
        "extracted_skills": skills,
        "education": education,
        "experience": experience,
        "projects": projects[:8],
        "certifications": certs,
        "links": {
            "github": github.group(0) if github else None,
            "linkedin": linkedin.group(0) if linkedin else None,
        },
        "completeness": completeness,
        "uncertain_fields": uncertain,
    }
