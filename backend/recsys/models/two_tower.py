from __future__ import annotations

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

from .base import BaseRecommender, Recommendation


class _InteractionDataset(Dataset):
    def __init__(
        self,
        interactions: pd.DataFrame,
        u_idx: dict,
        i_idx: dict,
        history_by_user: dict,
        max_history: int,
        item_genres: np.ndarray | None,
    ) -> None:
        self.pairs = [
            (u_idx[u], i_idx[i])
            for u, i in zip(interactions["user_id"], interactions["item_id"])
            if u in u_idx and i in i_idx
        ]
        self.history_by_user = history_by_user
        self.max_history = max_history
        self.item_genres = item_genres
        self.padding_idx = 0

    def __len__(self) -> int:
        return len(self.pairs)

    def __getitem__(self, idx: int) -> dict:
        u, i = self.pairs[idx]
        hist = self.history_by_user.get(u, [])
        if len(hist) > self.max_history:
            hist = hist[-self.max_history:]
        padded = [self.padding_idx] * (self.max_history - len(hist)) + [h + 1 for h in hist]
        out = {
            "user_id": u,
            "history_ids": torch.tensor(padded, dtype=torch.long),
            "pos_item_id": i,
        }
        if self.item_genres is not None:
            out["genres"] = self.item_genres[i]
        return out


def _collate(batch: list[dict], item_genres: np.ndarray | None) -> dict:
    user_ids = torch.tensor([b["user_id"] for b in batch], dtype=torch.long)
    history = torch.stack([b["history_ids"] for b in batch])
    pos = torch.tensor([b["pos_item_id"] for b in batch], dtype=torch.long)
    out = {"user_ids": user_ids, "history_ids": history, "pos_item_ids": pos}
    if item_genres is not None:
        genre_lists = [b["genres"] for b in batch]
        offsets = [0]
        flat: list[int] = []
        for g in genre_lists:
            flat.extend(g)
            offsets.append(offsets[-1] + len(g))
        out["genre_ids"] = torch.tensor(flat or [0], dtype=torch.long)
        out["genre_offsets"] = torch.tensor(offsets[:-1], dtype=torch.long)
    return out


class _UserTower(nn.Module):
    def __init__(self, n_items: int, n_users: int, embed_dim: int, mlp_dims: tuple, padding_idx: int = 0) -> None:
        super().__init__()
        self.item_emb = nn.Embedding(n_items + 1, embed_dim, padding_idx=padding_idx)
        self.user_emb = nn.Embedding(n_users, embed_dim)
        in_dim = embed_dim * 2
        layers: list[nn.Module] = []
        prev = in_dim
        for h in mlp_dims:
            layers += [nn.Linear(prev, h), nn.ReLU()]
            prev = h
        self.mlp = nn.Sequential(*layers)
        self.out_dim = prev

    def forward(self, history_ids: torch.Tensor, user_ids: torch.Tensor) -> torch.Tensor:
        mask = (history_ids != 0).float().unsqueeze(-1)
        h = self.item_emb(history_ids) * mask
        pooled = h.sum(dim=1) / mask.sum(dim=1).clamp(min=1.0)
        z = torch.cat([pooled, self.user_emb(user_ids)], dim=-1)
        return F.normalize(self.mlp(z), p=2, dim=-1)


class _ItemTower(nn.Module):
    def __init__(self, n_items: int, embed_dim: int, mlp_dims: tuple, n_genres: int | None = None) -> None:
        super().__init__()
        self.item_emb = nn.Embedding(n_items, embed_dim)
        self.use_genres = n_genres is not None and n_genres > 0
        if self.use_genres:
            self.genre_emb = nn.EmbeddingBag(n_genres, embed_dim, mode="mean")
            in_dim = embed_dim * 2
        else:
            in_dim = embed_dim
        layers: list[nn.Module] = []
        prev = in_dim
        for h in mlp_dims:
            layers += [nn.Linear(prev, h), nn.ReLU()]
            prev = h
        self.mlp = nn.Sequential(*layers)
        self.out_dim = prev

    def forward(
        self,
        item_ids: torch.Tensor,
        genre_ids: torch.Tensor | None = None,
        genre_offsets: torch.Tensor | None = None,
    ) -> torch.Tensor:
        x = self.item_emb(item_ids)
        if self.use_genres and genre_ids is not None:
            x = torch.cat([x, self.genre_emb(genre_ids, genre_offsets)], dim=-1)
        return F.normalize(self.mlp(x), p=2, dim=-1)


class TwoTowerRecommender(BaseRecommender):
    name = "two_tower"

    def __init__(
        self,
        embed_dim: int = 32,
        mlp_dims: tuple = (64, 32),
        max_history: int = 50,
        batch_size: int = 1024,
        epochs: int = 10,
        lr: float = 1e-3,
        temperature: float = 0.07,
        genre_col: str | None = None,
        device: str = "cpu",
        seed: int = 42,
    ) -> None:
        self.embed_dim = embed_dim
        self.mlp_dims = mlp_dims
        self.max_history = max_history
        self.batch_size = batch_size
        self.epochs = epochs
        self.lr = lr
        self.temperature = temperature
        self.genre_col = genre_col
        self.device = device
        self.seed = seed

        self._model: nn.Module | None = None
        self._u_idx: dict = {}
        self._i_idx: dict = {}
        self._item_ids: np.ndarray | None = None
        self._user_history: dict = {}
        self._user_seen: dict = {}
        self._item_genres_np: np.ndarray | None = None
        self._all_item_vecs: torch.Tensor | None = None

    def _build_indices(self, interactions: pd.DataFrame) -> None:
        users = interactions["user_id"].unique()
        items = interactions["item_id"].unique()
        self._u_idx = {u: i for i, u in enumerate(users)}
        self._i_idx = {it: i for i, it in enumerate(items)}
        self._item_ids = items

    def _build_history(self, interactions: pd.DataFrame) -> None:
        if "timestamp" in interactions.columns:
            ts = interactions["timestamp"].values.astype("int64")
            sorted_df = interactions.iloc[ts.argsort(kind="mergesort")]
        else:
            sorted_df = interactions
        history: dict = {}
        for u, grp in sorted_df.groupby("user_id"):
            if u not in self._u_idx:
                continue
            history[self._u_idx[u]] = [self._i_idx[i] for i in grp["item_id"] if i in self._i_idx]
        self._user_history = history

    def _build_item_genres(self, items: pd.DataFrame | None) -> tuple[np.ndarray | None, int]:
        if items is None or self.genre_col is None or self.genre_col not in items.columns:
            return None, 0
        vocab: dict = {}
        rows: list[list[int]] = [[] for _ in range(len(self._item_ids))]
        for _, row in items.iterrows():
            iid = row["item_id"]
            if iid not in self._i_idx:
                continue
            tags = row[self.genre_col]
            if not isinstance(tags, list):
                tags = [tags] if tags else []
            ids: list[int] = []
            for t in tags:
                if t not in vocab:
                    vocab[t] = len(vocab)
                ids.append(vocab[t])
            rows[self._i_idx[iid]] = ids
        item_genres_np = np.array(rows, dtype=object)
        return item_genres_np, len(vocab)

    def fit(
        self,
        interactions: pd.DataFrame,
        items: pd.DataFrame | None = None,
        users: pd.DataFrame | None = None,
    ) -> None:
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)

        self._build_indices(interactions)
        self._build_history(interactions)
        self._user_seen = interactions.groupby("user_id")["item_id"].apply(set).to_dict()
        self._item_genres_np, n_genres = self._build_item_genres(items)

        n_users = len(self._u_idx)
        n_items = len(self._i_idx)

        user_tower = _UserTower(n_items, n_users, self.embed_dim, self.mlp_dims)
        item_tower = _ItemTower(n_items, self.embed_dim, self.mlp_dims, n_genres=n_genres)
        assert user_tower.out_dim == item_tower.out_dim

        device = torch.device(self.device)
        self._model = nn.ModuleDict({"user": user_tower, "item": item_tower}).to(device)

        dataset = _InteractionDataset(
            interactions, self._u_idx, self._i_idx, self._user_history,
            self.max_history, self._item_genres_np,
        )
        loader = DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=True,
            collate_fn=lambda b: _collate(b, self._item_genres_np),
            num_workers=0,
        )

        optim = torch.optim.Adam(self._model.parameters(), lr=self.lr, weight_decay=1e-5)
        for _ in range(self.epochs):
            self._model.train()
            for batch in loader:
                user_ids = batch["user_ids"].to(device)
                history = batch["history_ids"].to(device)
                pos = batch["pos_item_ids"].to(device)
                g_ids = batch.get("genre_ids")
                g_offsets = batch.get("genre_offsets")
                if g_ids is not None:
                    g_ids = g_ids.to(device)
                    g_offsets = g_offsets.to(device)

                u_vec = self._model["user"](history, user_ids)
                v_vec = self._model["item"](pos, g_ids, g_offsets)
                logits = (u_vec @ v_vec.t()) / self.temperature
                labels = torch.arange(logits.size(0), device=device)
                loss = 0.5 * (F.cross_entropy(logits, labels) + F.cross_entropy(logits.t(), labels))

                optim.zero_grad()
                loss.backward()
                optim.step()

        self._cache_item_vectors(device)

    def _cache_item_vectors(self, device: torch.device) -> None:
        assert self._model is not None and self._item_ids is not None
        self._model.eval()
        n_items = len(self._item_ids)
        all_ids = torch.arange(n_items, dtype=torch.long, device=device)
        with torch.no_grad():
            if self._item_genres_np is None:
                vecs = self._model["item"](all_ids).cpu()
            else:
                chunks = []
                bs = 512
                for start in range(0, n_items, bs):
                    end = min(start + bs, n_items)
                    ids = all_ids[start:end]
                    glist = [self._item_genres_np[i] for i in range(start, end)]
                    offsets = [0]
                    flat: list[int] = []
                    for g in glist:
                        flat.extend(g)
                        offsets.append(offsets[-1] + len(g))
                    g_ids = torch.tensor(flat or [0], dtype=torch.long, device=device)
                    g_off = torch.tensor(offsets[:-1], dtype=torch.long, device=device)
                    chunks.append(self._model["item"](ids, g_ids, g_off).cpu())
                vecs = torch.cat(chunks, dim=0)
        self._all_item_vecs = vecs

    def recommend(
        self,
        user_id: int | str,
        k: int = 10,
        exclude_seen: bool = True,
    ) -> list[Recommendation]:
        if user_id not in self._u_idx or self._model is None or self._all_item_vecs is None:
            return []
        device = torch.device(self.device)
        u = self._u_idx[user_id]
        hist = self._user_history.get(u, [])
        if len(hist) > self.max_history:
            hist = hist[-self.max_history:]
        padded = [0] * (self.max_history - len(hist)) + [h + 1 for h in hist]
        history_tensor = torch.tensor([padded], dtype=torch.long, device=device)
        user_tensor = torch.tensor([u], dtype=torch.long, device=device)

        self._model.eval()
        with torch.no_grad():
            u_vec = self._model["user"](history_tensor, user_tensor).cpu()
        scores = (u_vec @ self._all_item_vecs.t()).numpy().ravel()

        if exclude_seen:
            for iid in self._user_seen.get(user_id, set()):
                if iid in self._i_idx:
                    scores[self._i_idx[iid]] = -np.inf

        top = np.argsort(-scores)[:k]
        assert self._item_ids is not None
        return [
            Recommendation(item_id=self._item_ids[i], score=float(scores[i]))
            for i in top
            if np.isfinite(scores[i])
        ]
