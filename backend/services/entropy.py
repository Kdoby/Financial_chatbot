"""
Semantic Entropy 모듈
Farquhar et al. (Nature 2024) 방식 구현.

Claude API는 log prob을 제공하지 않으므로 count 기반 근사:
  P(C_c | q) ≈ |C_c| / N
이 방식도 의미적 다양성을 잘 포착함.

클러스터링: SBERT 대신 한국어 character 2-gram Jaccard 유사도 사용
(외부 ML 의존성 제거 — torch/sentence-transformers 불필요)
"""

from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass
class SEResult:
    semantic_entropy: float
    n_clusters: int
    cluster_sizes: list[int]
    answers: list[str]
    labels: list[int]
    is_uncertain: bool
    confidence: str

    @property
    def normalized_se(self) -> float:
        n = len(self.answers)
        if n <= 1:
            return 0.0
        return self.semantic_entropy / math.log(n)


SE_THRESHOLD_LOW = 0.3
SE_THRESHOLD_HIGH = 0.6


def _char_bigram_jaccard(a: str, b: str) -> float:
    """character 2-gram Jaccard 유사도 — 한국어 형태소 분리 없이도 의미 근접도 포착"""
    def bigrams(text: str) -> set[str]:
        t = text.replace(" ", "")
        return {t[i:i+2] for i in range(len(t) - 1)}

    sa, sb = bigrams(a), bigrams(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


class SemanticEntropyCalculator:
    def __init__(self, similarity_threshold: float = 0.4):
        self.similarity_threshold = similarity_threshold

    def _cluster(self, answers: list[str]) -> list[int]:
        n = len(answers)
        parent = list(range(n))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for i in range(n):
            for j in range(i + 1, n):
                if _char_bigram_jaccard(answers[i], answers[j]) >= self.similarity_threshold:
                    parent[find(i)] = find(j)

        # 루트 ID → 0부터 시작하는 연속 레이블로 변환
        root_to_label: dict[int, int] = {}
        labels = []
        for i in range(n):
            root = find(i)
            if root not in root_to_label:
                root_to_label[root] = len(root_to_label)
            labels.append(root_to_label[root])
        return labels

    def compute(self, answers: list[str]) -> SEResult:
        answers = [a.strip() for a in answers if a.strip()]
        n = len(answers)
        if n == 0:
            return SEResult(0.0, 0, [], [], [], False, "높음")

        labels = self._cluster(answers)
        unique_labels = set(labels)
        n_clusters = len(unique_labels)

        cluster_sizes = [labels.count(c) for c in unique_labels]
        cluster_probs = [s / n for s in cluster_sizes]

        se = -sum(p * math.log(p) for p in cluster_probs if p > 1e-12)
        norm_se = se / math.log(n) if n > 1 else 0.0

        if norm_se < SE_THRESHOLD_LOW:
            confidence, is_uncertain = "높음", False
        elif norm_se < SE_THRESHOLD_HIGH:
            confidence, is_uncertain = "보통", False
        else:
            confidence, is_uncertain = "낮음", True

        return SEResult(
            semantic_entropy=se,
            n_clusters=n_clusters,
            cluster_sizes=cluster_sizes,
            answers=answers,
            labels=labels,
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
