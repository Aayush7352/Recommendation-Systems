from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from recsys.models.base import Recommendation
from recsys.models.popularity import PopularityRecommender


@pytest.fixture
def interactions() -> pd.DataFrame:
    return pd.DataFrame({
        "user_id": ["u1", "u1", "u2", "u2", "u3", "u3", "u4"],
        "item_id": ["i1", "i2", "i1", "i3", "i2", "i4", "i5"],
        "rating": [5, 3, 4, 2, 1, 5, 3],
        "timestamp": pd.to_datetime([
            "2021-01-01", "2021-01-02", "2021-01-01",
            "2021-01-03", "2021-01-02", "2021-01-04", "2021-01-05",
        ]),
    })


class TestPopularityRecommender:
    def test_recommend_returns_recommendation_objects(self, interactions):
        model = PopularityRecommender()
        model.fit(interactions)
        recs = model.recommend("u1", k=3)
        assert all(isinstance(r, Recommendation) for r in recs)

    def test_exclude_seen(self, interactions):
        model = PopularityRecommender()
        model.fit(interactions)
        recs = model.recommend("u1", k=5, exclude_seen=True)
        seen = {"i1", "i2"}
        rec_ids = {r.item_id for r in recs}
        assert seen.isdisjoint(rec_ids)

    def test_scores_descending(self, interactions):
        model = PopularityRecommender()
        model.fit(interactions)
        recs = model.recommend("u1", k=5)
        scores = [r.score for r in recs]
        assert all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))

    def test_recommend_batch(self, interactions):
        model = PopularityRecommender()
        model.fit(interactions)
        results = model.recommend_batch(["u1", "u2"], k=2)
        assert set(results.keys()) == {"u1", "u2"}
