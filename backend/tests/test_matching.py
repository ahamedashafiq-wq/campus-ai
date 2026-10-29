from app.ai.matching import MatchInput, compute_match, coverage_score, skill_gap_report, weighted_total
from app.ai.taxonomy import extract_skills_from_text


def test_weighted_score_calculation():
    total = weighted_total(100, 0, 0, 0)
    assert total == 40.0
    total = weighted_total(50, 100, 100, 100)
    assert total == 80.0
    redistributed = weighted_total(100, 100, 0, 100, semantic_available=False)
    assert redistributed == 100.0


def test_required_skill_coverage_uses_actual_skills():
    score, matched, missing = coverage_score({"python", "sql"}, ["python", "java", "sql"])
    assert matched == ["python", "sql"] or set(matched) == {"python", "sql"}
    assert "java" in missing
    assert score == round(200 / 3, 2) or abs(score - 66.67) < 0.1


def test_compute_match_explainable():
    result = compute_match(
        MatchInput(
            student_skills=["python", "fastapi", "sql"],
            required_skills=["python", "sql", "docker"],
            preferred_skills=["react"],
            student_text="Built a FastAPI service with PostgreSQL and unit tests.",
            job_text="Looking for Python FastAPI engineers with SQL and Docker.",
            projects=["Campus placement API"],
            graduation_year=2026,
            min_graduation_year=2025,
            max_graduation_year=2027,
        )
    )
    assert 0 <= result["overall_score"] <= 100
    assert "python" in result["matched_required_skills"]
    assert "docker" in result["missing_required_skills"]
    assert result["eligibility"] == "eligible"
    assert result["matching_method"] in {"semantic_weighted", "tfidf_weighted", "skill_only"}
    gap = skill_gap_report(result)
    assert "docker" in gap["missing_required_skills"]
    assert "guarantee" in gap["verified_vs_advice"]["advice"].lower() or "does not guarantee" in gap["verified_vs_advice"]["advice"]


def test_missing_info_is_unknown_not_ineligible():
    result = compute_match(
        MatchInput(
            student_skills=["python"],
            required_skills=["python"],
            preferred_skills=[],
            student_text="python intern",
            job_text="python intern",
            min_cgpa=7.0,
            cgpa=None,
        )
    )
    assert result["eligibility"] == "unknown"


def test_skill_extraction_does_not_invent():
    skills = extract_skills_from_text("I used Python and React to build dashboards in Tableau.")
    slugs = {s["slug"] for s in skills}
    assert "python" in slugs
    assert "react" in slugs
    assert "tableau" in slugs
    assert "cobol" not in slugs
