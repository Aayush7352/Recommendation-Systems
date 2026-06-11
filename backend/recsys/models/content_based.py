from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MultiLabelBinarizer

from .base import BaseRecommender, Recommendation


def _build_text_corpus(items: pd.DataFrame, text_cols: list[str]) -> list[str]:
    parts = [items[c].fillna("").astype(str) for c in text_cols if c in items.columns]
    if not parts:
        return [""] * len(items)
    return parts[0].str.cat(parts[1:], sep=" ").tolist()


class ContentBasedRecommender(BaseRecommender):
    name = "content_based"

    def __init__(
        self,
        text_cols: list[str] | None = None,
        tags_col: str | None = None,
        min_rating_for_profile: float = 4.0,
    ) -> None:
        self.text_cols = text_cols or []
        self.tags_col = tags_col
        self.min_rating_for_profile = min_rating_for_profile
        self._item_features: np.ndarray | None = None
        self._item_ids: np.ndarray | None = None
        self._item_id_to_idx: dict = {}
        self._user_profiles: dict = {}
        self._user_seen: dict = {}

    def fit(
        self,
        interactions: pd.DataFrame,
        items: pd.DataFrame | None = None,
        users: pd.DataFrame | None = None,
    ) -> None:
        if items is None:
            raise ValueError("ContentBasedRecommender requires an items DataFrame")

        items = items.reset_index(drop=True).copy()
        self._item_ids = items["item_id"].to_numpy()
        self._item_id_to_idx = {iid: i for i, iid in enumerate(self._item_ids)}

        feature_blocks: list = []

        if self.text_cols:
            corpus = _build_text_corpus(items, self.text_cols)
            tfidf = TfidfVectorizer(max_features=5000, stop_words="english", ngram_range=(1, 2))
            text_mat = tfidf.fit_transform(corpus)
            feature_blocks.append(text_mat)

        if self.tags_col and self.tags_col in items.columns:
            mlb = MultiLabelBinarizer(sparse_output=True)
            tag_lists = items[self.tags_col].apply(lambda x: x if isinstance(x, list) else [])
            tag_mat = mlb.fit_transform(tag_lists)
            feature_blocks.append(tag_mat)

        if not feature_blocks:
            raise ValueError("No feature columns produced features; set text_cols or tags_col")

        from scipy.sparse import hstack
        mat = hstack(feature_blocks).tocsr() if len(feature_blocks) > 1 else feature_blocks[0]
        norms = np.sqrt(mat.multiply(mat).sum(axis=1))
        norms = np.asarray(norms).ravel()
        norms[norms == 0] = 1.0
        inv = csr_matrix(np.diag(1.0 / norms))
        self._item_features = inv @ mat

        self._user_seen = interactions.groupby("user_id")["item_id"].apply(set).to_dict()
        liked = interactions[interactions["rating"] >= self.min_rating_for_profile] \
            if "rating" in interactions.columns else interactions

        for uid, grp in liked.groupby("user_id"):
            idxs = [self._item_id_to_idx[i] for i in grp["item_id"] if i in self._item_id_to_idx]
            if not idxs:
                continue
            profile = self._item_features[idxs].mean(axis=0)
            self._user_profiles[uid] = np.asarray(profile).ravel()

    def recommend(
        self,
        user_id: int | str,
        k: int = 10,
        exclude_seen: bool = True,
    ) -> list[Recommendation]:
        if user_id not in self._user_profiles:
            return []
        profile = self._user_profiles[user_id].reshape(1, -1)
        sims = cosine_similarity(profile, self._item_features).ravel()
        seen = self._user_seen.get(user_id, set()) if exclude_seen else set()

        ranked = np.argsort(-sims)
        out: list[Recommendation] = []
        for idx in ranked:
            iid = self._item_ids[idx]
            if iid in seen:
                continue
            out.append(Recommendation(item_id=iid, score=float(sims[idx])))
            if len(out) == k:
                break
        return out
