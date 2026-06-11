from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

from .base import BaseRecommender, Recommendation


def _build_interaction_matrix(
    interactions: pd.DataFrame,
) -> tuple[csr_matrix, dict, dict, np.ndarray, np.ndarray]:
    user_ids = interactions["user_id"].unique()
    item_ids = interactions["item_id"].unique()
    u_idx = {u: i for i, u in enumerate(user_ids)}
    i_idx = {it: i for i, it in enumerate(item_ids)}

    rows = interactions["user_id"].map(u_idx).to_numpy()
    cols = interactions["item_id"].map(i_idx).to_numpy()
    if "rating" in interactions.columns:
        vals = interactions["rating"].astype(np.float32).to_numpy()
    else:
        vals = np.ones(len(interactions), dtype=np.float32)

    mat = csr_matrix((vals, (rows, cols)), shape=(len(user_ids), len(item_ids)))
    return mat, u_idx, i_idx, user_ids, item_ids


class ItemKNNRecommender(BaseRecommender):
    name = "item_knn"

    def __init__(self, k_neighbors: int = 50) -> None:
        self.k_neighbors = k_neighbors
        self._sim: np.ndarray | None = None
        self._mat: csr_matrix | None = None
        self._u_idx: dict = {}
        self._i_idx: dict = {}
        self._item_ids: np.ndarray | None = None

    def fit(
        self,
        interactions: pd.DataFrame,
        items: pd.DataFrame | None = None,
        users: pd.DataFrame | None = None,
    ) -> None:
        mat, u_idx, i_idx, _, item_ids = _build_interaction_matrix(interactions)
        self._mat = mat
        self._u_idx = u_idx
        self._i_idx = i_idx
        self._item_ids = item_ids

        item_mat = mat.T.tocsr().astype(np.float32)
        norms = np.sqrt(np.asarray(item_mat.multiply(item_mat).sum(axis=1)).ravel())
        norms[norms == 0] = 1.0
        normed = item_mat.multiply(1.0 / norms[:, None]).tocsr()
        sim = (normed @ normed.T).toarray()
        np.fill_diagonal(sim, 0.0)

        if self.k_neighbors < sim.shape[1]:
            kth = sim.shape[1] - self.k_neighbors
            thresh = np.partition(sim, kth, axis=1)[:, kth][:, None]
            sim[sim < thresh] = 0.0
        self._sim = sim.astype(np.float32)

    def recommend(
        self,
        user_id: int | str,
        k: int = 10,
        exclude_seen: bool = True,
    ) -> list[Recommendation]:
        if user_id not in self._u_idx or self._sim is None or self._mat is None:
            return []
        u = self._u_idx[user_id]
        user_row = self._mat[u].toarray().ravel()
        scores = user_row @ self._sim
        if exclude_seen:
            scores[user_row > 0] = -np.inf

        ranked = np.argsort(-scores)[:k]
        return [
            Recommendation(item_id=self._item_ids[i], score=float(scores[i]))
            for i in ranked
            if np.isfinite(scores[i])
        ]


class ALSRecommender(BaseRecommender):
    name = "als"

    def __init__(
        self,
        factors: int = 64,
        regularization: float = 0.01,
        iterations: int = 20,
        alpha: float = 40.0,
    ) -> None:
        self.factors = factors
        self.regularization = regularization
        self.iterations = iterations
        self.alpha = alpha
        self._model = None
        self._mat: csr_matrix | None = None
        self._u_idx: dict = {}
        self._item_ids: np.ndarray | None = None

    def fit(
        self,
        interactions: pd.DataFrame,
        items: pd.DataFrame | None = None,
        users: pd.DataFrame | None = None,
    ) -> None:
        import os
        os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
        from implicit.als import AlternatingLeastSquares

        mat, u_idx, i_idx, _, item_ids = _build_interaction_matrix(interactions)
        self._mat = (mat * self.alpha).astype(np.float32).tocsr()
        self._u_idx = u_idx
        self._item_ids = item_ids
        _ = i_idx

        self._model = AlternatingLeastSquares(
            factors=self.factors,
            regularization=self.regularization,
            iterations=self.iterations,
            use_gpu=False,
        )
        self._model.fit(self._mat, show_progress=False)

    def recommend(
        self,
        user_id: int | str,
        k: int = 10,
        exclude_seen: bool = True,
    ) -> list[Recommendation]:
        if user_id not in self._u_idx or self._model is None or self._mat is None:
            return []
        u = self._u_idx[user_id]
        ids, scores = self._model.recommend(
            u, self._mat[u], N=k, filter_already_liked_items=exclude_seen,
        )
        return [
            Recommendation(item_id=self._item_ids[int(i)], score=float(s))
            for i, s in zip(ids, scores)
        ]
