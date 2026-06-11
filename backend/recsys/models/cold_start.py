from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from ..vector_store import VectorStore
from .base import BaseRecommender, Recommendation


class ColdStartRecommender(BaseRecommender):
    name = "cold_start"

    def __init__(
        self,
        text_cols: list[str] | None = None,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
    ):
        self.text_cols = text_cols or ["title", "abstract", "category"]
        self._vectorizer = TfidfVectorizer(max_features=512, stop_words="english")
        self._vector_store = VectorStore(host=qdrant_host, port=qdrant_port)
        self._item_ids: np.ndarray | None = None
        self._text_features: np.ndarray | None = None

    def fit(
        self,
        interactions: pd.DataFrame,
        items: pd.DataFrame | None = None,
        users: pd.DataFrame | None = None,
    ) -> None:
        if items is None:
            raise ValueError("ColdStartRecommender requires an items DataFrame")
        items = items.reset_index(drop=True).copy()
        self._item_ids = items["item_id"].to_numpy()

        corpus = self._build_corpus(items)
        self._text_features = self._vectorizer.fit_transform(corpus).toarray().astype(np.float32)
        self._vector_store.index_cold_start_items(items, self._text_features)

    def _build_corpus(self, items: pd.DataFrame) -> list[str]:
        parts = [items[c].fillna("").astype(str) for c in self.text_cols if c in items.columns]
        if not parts:
            return [""] * len(items)
        return parts[0].str.cat(parts[1:], sep=" ").tolist()

    def recommend(
        self,
        user_id: int | str,
        k: int = 10,
        exclude_seen: bool = True,
    ) -> list[Recommendation]:
        return []

    def recommend_from_text(self, query: str, k: int = 10) -> list[Recommendation]:
        vec = self._vectorizer.transform([query]).toarray().ravel().astype(np.float32)
        return self._vector_store.cold_start_search(vec, k=k)
