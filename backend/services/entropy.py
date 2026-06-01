"""
Semantic Entropy 모듈
Farquhar et al. (Nature 2024) 방식 구현.

Claude API는 log prob을 제공하지 않으므로 count 기반 근사:
  P(C_c | q) ≈ |C_c| / N
이 방식도 의미적 다양성을 잘 포착함.
"""

from __future__ import annotations
import math
from dataclasses import dataclass

import numpy as np


@dataclass
class SEResult:
    semantic_entropy: float          # 핵심 지표
    n_clusters: int                  # 의미 클러스터 수
    cluster_sizes: list[int]         # 각 클러스터 크기
    answers: list[str]               # 샘플 답변들
    labels: list[int]                # 클러스터 레이블
    is_uncertain: bool               # SE > threshold
    confidence: str                  # "높음" / "보통" / "낮음"

    @property
    def normalized_se(self) -> float:
        """SE를 [0, 1] 범위로 정규화 (log N 기준)"""
        n = len(self.answers)
        if n <= 1:
            return 0.0
        return self.semantic_entropy / math.log(n)


SE_THRESHOLD_LOW = 0.3     # 정규화 SE < 0.3 → 높은 확신
SE_THRESHOLD_HIGH = 0.6    # 정규화 SE > 0.6 → 낮은 확신


class SemanticEntropyCalculator:
    def __init__(self, sbert_threshold: float = 0.75):
        self.sbert_threshold = sbert_threshold
        self._sbert_model = None

    def _get_sbert(self):
        if self._sbert_model is None:
            from core.sbert import get_sbert
            self._sbert_model = get_sbert()
        return self._sbert_model

    def _cluster(self, answers: list[str]) -> np.ndarray:
        from sklearn.cluster import AgglomerativeClustering
        from sklearn.metrics.pairwise import cosine_similarity

        n = len(answers)
        if n == 1:
            return np.array([0])

        model = self._get_sbert()
        embeddings = model.encode(answers, normalize_embeddings=True)
        dist = np.clip(1 - cosine_similarity(embeddings), 0, 2).astype("float64")

        labels = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=1 - self.sbert_threshold,
            metric="precomputed",
            linkage="average",
        ).fit_predict(dist)
        return labels

    def compute(self, answers: list[str]) -> SEResult:
        """답변 목록으로 SE 계산"""
        answers = [a.strip() for a in answers if a.strip()]
        n = len(answers)
        if n == 0:
            return SEResult(0.0, 0, [], [], [], False, "높음")

        labels = self._cluster(answers)
        unique_labels = np.unique(labels)
        n_clusters = len(unique_labels)

        # count 기반 클러스터 확률
        cluster_probs = {
            int(c): int(np.sum(labels == c)) / n for c in unique_labels
        }
        cluster_sizes = [int(np.sum(labels == c)) for c in unique_labels]

        se = -sum(p * math.log(p) for p in cluster_probs.values() if p > 1e-12)

        # [0,1] 정규화
        norm_se = se / math.log(n) if n > 1 else 0.0

        if norm_se < SE_THRESHOLD_LOW:
            confidence = "높음"
            is_uncertain = False
        elif norm_se < SE_THRESHOLD_HIGH:
            confidence = "보통"
            is_uncertain = False
        else:
            confidence = "낮음"
            is_uncertain = True

        return SEResult(
            semantic_entropy=se,
            n_clusters=n_clusters,
            cluster_sizes=cluster_sizes,
            answers=answers,
            labels=labels.tolist(),
            is_uncertain=is_uncertain,
            confidence=confidence,
        )


# 싱글턴
_calc: SemanticEntropyCalculator | None = None


def get_calculator() -> SemanticEntropyCalculator:
    global _calc
    if _calc is None:
        _calc = SemanticEntropyCalculator()
    return _calc
