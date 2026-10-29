"""Optional LLM provider interface. Core matching never depends on this."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.config import get_settings

log = logging.getLogger(__name__)


class LlmUnavailable(Exception):
    pass


def llm_status() -> dict[str, Any]:
    s = get_settings()
    configured = s.llm_provider != "none" and bool(s.llm_api_key)
    return {"provider": s.llm_provider, "configured": configured, "model": s.llm_model or None}


def generate_advice(prompt: str) -> dict[str, Any]:
    """Return structured advice or an explicit disabled/error status. Never invent success."""
    s = get_settings()
    if s.llm_provider == "none" or not s.llm_api_key:
        return {"enabled": False, "text": None, "reason": "LLM provider is not configured"}
    url = s.llm_base_url or "https://api.openai.com/v1/chat/completions"
    try:
        with httpx.Client(timeout=s.llm_timeout_seconds) as client:
            response = client.post(
                url,
                headers={"Authorization": f"Bearer {s.llm_api_key}", "Content-Type": "application/json"},
                json={
                    "model": s.llm_model or "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You give learning suggestions. You cannot override skill-gap facts. Do not claim placement guarantees.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                },
            )
            response.raise_for_status()
            data = response.json()
            text = data["choices"][0]["message"]["content"]
            return {"enabled": True, "text": text, "reason": None}
    except Exception as exc:
        log.warning("LLM request failed: %s", exc)
        return {"enabled": False, "text": None, "reason": "llm_request_failed"}


def parse_json_object(raw: str) -> dict[str, Any] | None:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None
