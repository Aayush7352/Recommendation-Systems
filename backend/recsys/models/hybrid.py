from __future__ import annotations

from collections import defaultdict

import pandas as pd

from .base import BaseRecommender, Recommendation


def _normalize_scores(recs: list[Recommendation]) -> dict:
    if not recs:
        return {}
    scores = [r.score for r in recs]
    lo, hi = min(scores), max(scores)
    span = hi - lo or 1.0
    return {r.item_id: (r.score - lo) / span for r in recs}


class HybridRecommender(BaseRecommender):
    name = "hybrid"

    def __init__(
        self,
        components: list[tuple[BaseRecommender, float]],
        candidate_multiplier: int = 5,
    ) -> None:
        if not components:
            raise ValueError("HybridRecommender requires at least one component")
        self.components = components
        self.candidate_multiplier = candidate_multiplier

    def fit(
        self,
        interactions: pd.DataFrame,
        items: pd.DataFrame | None = None,
        users: pd.DataFrame | None = None,
    ) -> None:
        for model, _ in self.components:
            model.fit(interactions, items=items, users=users)

    def recommend(
        self,
        user_id: int | str,
        k: int = 10,
        exclude_seen: bool = True,
    ) -> list[Recommendation]:
        candidate_k = k * self.candidate_multiplier
        blended: dict = defaultdict(float)
        for model, weight in self.components:
            recs = model.recommend(user_id, k=candidate_k, exclude_seen=exclude_seen)
            normed = _normalize_scores(recs)
            for iid, score in normed.items():
                blended[iid] += weight * score

        ranked = sorted(blended.items(), key=lambda kv: -kv[1])[:k]
        return [Recommendation(item_id=iid, score=float(s)) for iid, s in ranked]
