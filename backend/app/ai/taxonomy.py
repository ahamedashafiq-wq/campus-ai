from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

TAXONOMY_PATH = Path(__file__).with_name("skill_taxonomy.json")


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9+#]+", " ", text.lower()).strip()


@lru_cache
def load_taxonomy() -> dict:
    with TAXONOMY_PATH.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache
def alias_index() -> dict[str, dict]:
    tax = load_taxonomy()
    index: dict[str, dict] = {}
    for skill in tax["skills"]:
        names = [skill["name"], skill["slug"], *skill.get("aliases", [])]
        for name in names:
            index[_normalize(name)] = skill
    return index


def lookup_skill(term: str) -> Optional[dict]:
    key = _normalize(term)
    if not key:
        return None
    return alias_index().get(key)


def extract_skills_from_text(text: str) -> list[dict]:
    """Dictionary matching with word-boundary-ish checks. Never invents skills."""
    if not text:
        return []
    lowered = text.lower()
    found: dict[str, dict] = {}
    for alias, skill in alias_index().items():
        if not alias:
            continue
        pattern = r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])"
        if re.search(pattern, lowered):
            found[skill["slug"]] = {
                "slug": skill["slug"],
                "name": skill["name"],
                "category": skill["category"],
                "source": "extracted",
            }
    return sorted(found.values(), key=lambda s: s["name"].lower())
