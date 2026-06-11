from __future__ import annotations

import pandas as pd

from .base import BaseRecommender, Recommendation


class PopularityRecommender(BaseRecommender):
    name = "popularity"

    def __init__(self) -> None:
        self._ranked: list[tuple] = []
        self._user_seen: dict = {}

    def fit(
        self,
        interactions: pd.DataFrame,
        items: pd.DataFrame | None = None,
        users: pd.DataFrame | None = None,
    ) -> None:
        counts = interactions.groupby("item_id").size().sort_values(ascending=False)
        max_count = counts.iloc[0] if len(counts) else 1
        self._ranked = [(iid, float(c) / float(max_count)) for iid, c in counts.items()]
        self._user_seen = interactions.groupby("user_id")["item_id"].apply(set).to_dict()

    def recommend(
        self,
        user_id: int | str,
        k: int = 10,
        exclude_seen: bool = True,
    ) -> list[Recommendation]:
        seen = self._user_seen.get(user_id, set()) if exclude_seen else set()
        out: list[Recommendation] = []
        for iid, score in self._ranked:
            if iid in seen:
                continue
            out.append(Recommendation(item_id=iid, score=score))
            if len(out) == k:
                break
        return out
