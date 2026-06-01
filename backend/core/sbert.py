"""SBERT 모델 싱글턴 — rag.py 와 semantic_entropy.py 공유"""
from __future__ import annotations

_model = None
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def get_sbert():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model
