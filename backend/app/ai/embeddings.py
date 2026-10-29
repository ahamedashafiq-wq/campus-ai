from __future__ import annotations

import threading
from typing import Optional

from app.config import get_settings

_lock = threading.Lock()
_model = None
_status = "uninitialized"
_error: Optional[str] = None


def embedding_status() -> dict:
    return {"status": _status, "error": _error, "model": get_settings().embedding_model}


def _load_model() -> None:
    global _model, _status, _error
    settings = get_settings()
    if not settings.embedding_enabled:
        _status = "disabled"
        return
    try:
        from sentence_transformers import SentenceTransformer

        name = settings.embedding_model_path or settings.embedding_model
        _status = "loading"
        _model = SentenceTransformer(name)
        _status = "ready"
        _error = None
    except Exception as exc:  # model missing, no network, incompatible torch, etc.
        _model = None
        _status = "unavailable"
        _error = str(exc)[:300]


def ensure_model_loaded() -> None:
    global _status
    if _status in {"ready", "unavailable", "disabled"}:
        return
    with _lock:
        if _status in {"ready", "unavailable", "disabled"}:
            return
        _load_model()


def encode_text(text: str) -> Optional[list[float]]:
    ensure_model_loaded()
    if _model is None or not text.strip():
        return None
    vector = _model.encode(text[:8000], normalize_embeddings=True)
    return vector.astype(float).tolist()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    import math

    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (na * nb)))
