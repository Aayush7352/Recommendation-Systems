from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import numpy as np


@dataclass
class EvalReport:
    algo: str
    k: int
    precision: float
    recall: float
    ndcg: float
    coverage: float
    diversity: float
    novelty: float
    n_users_evaluated: int

    def as_dict(self) -> dict:
        return {
            "algo": self.algo,
            "k": self.k,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "ndcg": round(self.ndcg, 4),
            "coverage": round(self.coverage, 4),
            "diversity": round(self.diversity, 4),
            "novelty": round(self.novelty, 4),
            "n_users_evaluated": self.n_users_evaluated,
        }


def precision_at_k(recs: list, truth: set, k: int) -> float:
    if k == 0:
        return 0.0
    hits = sum(1 for r in recs[:k] if r in truth)
    return hits / k


def recall_at_k(recs: list, truth: set, k: int) -> float:
    if not truth:
        return 0.0
    hits = sum(1 for r in recs[:k] if r in truth)
    return hits / len(truth)


def ndcg_at_k(recs: list, truth: set, k: int) -> float:
    if not truth:
        return 0.0
    dcg = 0.0
    for i, item in enumerate(recs[:k]):
        if item in truth:
            dcg += 1.0 / np.log2(i + 2)
    ideal_hits = min(len(truth), k)
    idcg = sum(1.0 / np.log2(i + 2) for i in range(ideal_hits))
    return dcg / idcg if idcg > 0 else 0.0


def coverage(all_recs: list[list], n_items: int) -> float:
    recommended = set()
    for r in all_recs:
        recommended.update(r)
    return len(recommended) / n_items if n_items > 0 else 0.0


def diversity(all_recs: list[list]) -> float:
    # Formula: 1 - mean pairwise Jaccard similarity across user reclists.
    if len(all_recs) < 2:
        return 0.0
    sims = []
    sample = all_recs[: min(200, len(all_recs))]
    for i in range(len(sample)):
        for j in range(i + 1, len(sample)):
            a, b = set(sample[i]), set(sample[j])
            union = a | b
            sims.append(len(a & b) / len(union) if union else 0.0)
    return 1.0 - float(np.mean(sims)) if sims else 0.0


def novelty(all_recs: list[list], item_popularity: dict) -> float:
    # Formula: mean self-information = mean(-log2(p(item))) across all recs.
    total = sum(item_popularity.values()) or 1
    score = 0.0
    n = 0
    for r in all_recs:
        for item in r:
            p = item_popularity.get(item, 1) / total
            score += -np.log2(p) if p > 0 else 0.0
            n += 1
    return score / n if n else 0.0


def evaluate(
    recommendations: dict,
    ground_truth: dict,
    k: int,
    n_items: int,
    item_popularity: dict | None = None,
    algo_name: str = "unknown",
) -> EvalReport:
    users = [u for u in ground_truth if u in recommendations and ground_truth[u]]
    if not users:
        return EvalReport(algo_name, k, 0, 0, 0, 0, 0, 0, 0)

    precisions, recalls, ndcgs = [], [], []
    all_rec_lists = []
    for u in users:
        raw = recommendations[u]
        recs = [r.item_id for r in raw] if raw and hasattr(raw[0], "item_id") else list(raw)
        truth = ground_truth[u]
        precisions.append(precision_at_k(recs, truth, k))
        recalls.append(recall_at_k(recs, truth, k))
        ndcgs.append(ndcg_at_k(recs, truth, k))
        all_rec_lists.append(recs[:k])

    pop = item_popularity or Counter()

    return EvalReport(
        algo=algo_name,
        k=k,
        precision=float(np.mean(precisions)),
        recall=float(np.mean(recalls)),
        ndcg=float(np.mean(ndcgs)),
        coverage=coverage(all_rec_lists, n_items),
        diversity=diversity(all_rec_lists),
        novelty=novelty(all_rec_lists, dict(pop)),
        n_users_evaluated=len(users),
    )
