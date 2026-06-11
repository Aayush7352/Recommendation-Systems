from __future__ import annotations

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

from .base import BaseRecommender, Recommendation


class _SessionDataset(Dataset):
    def __init__(self, sessions: list[list[int]], n_items: int, max_len: int = 50):
        self.sessions = sessions
        self.n_items = n_items
        self.max_len = max_len

    def __len__(self) -> int:
        return len(self.sessions)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        session = self.sessions[idx]
        if len(session) > self.max_len:
            session = session[-self.max_len:]
        x = torch.tensor(session[:-1], dtype=torch.long)
        y = torch.tensor(session[-1], dtype=torch.long)
        return x, y


def _collate_sessions(batch: list[tuple[torch.Tensor, torch.Tensor]]) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    xs, ys = zip(*batch)
    lengths = torch.tensor([len(x) for x in xs])
    padded = torch.nn.utils.rnn.pad_sequence(xs, batch_first=True, padding_value=0)
    return padded, lengths, torch.tensor(ys, dtype=torch.long)


class _GRU4Rec(nn.Module):
    def __init__(self, n_items: int, embed_dim: int = 64, hidden_dim: int = 100, num_layers: int = 1):
        super().__init__()
        self.embedding = nn.Embedding(n_items + 1, embed_dim, padding_idx=0)
        self.gru = nn.GRU(embed_dim, hidden_dim, num_layers, batch_first=True)
        self.out = nn.Linear(hidden_dim, n_items)

    def forward(self, x: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        emb = self.embedding(x)
        packed = nn.utils.rnn.pack_padded_sequence(emb, lengths.cpu(), batch_first=True, enforce_sorted=False)
        _, hidden = self.gru(packed)
        return self.out(hidden[-1])


class GRU4RecRecommender(BaseRecommender):
    name = "gru4rec"

    def __init__(
        self,
        embed_dim: int = 64,
        hidden_dim: int = 100,
        num_layers: int = 1,
        max_session_len: int = 50,
        epochs: int = 10,
        batch_size: int = 128,
        lr: float = 1e-3,
        device: str = "cpu",
        seed: int = 42,
    ):
        self.embed_dim = embed_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.max_session_len = max_session_len
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.device = device
        self.seed = seed

        self._model: nn.Module | None = None
        self._i_idx: dict = {}
        self._item_ids: np.ndarray | None = None
        self._item_popularity: np.ndarray | None = None

    def fit(
        self,
        interactions: pd.DataFrame,
        items: pd.DataFrame | None = None,
        users: pd.DataFrame | None = None,
    ) -> None:
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)

        all_items = interactions["item_id"].unique()
        self._i_idx = {it: i + 1 for i, it in enumerate(all_items)}
        self._item_ids = all_items
        n_items = len(self._item_ids)

        item_counts = interactions["item_id"].value_counts()
        self._item_popularity = np.array([item_counts.get(it, 0) for it in self._item_ids], dtype=np.float32)
        self._item_popularity = self._item_popularity / self._item_popularity.sum()

        if "timestamp" in interactions.columns:
            ts = interactions["timestamp"].values.astype("int64")
            interactions = interactions.iloc[ts.argsort()]

        sessions = []
        for _, grp in interactions.groupby("user_id"):
            session = [self._i_idx[i] for i in grp["item_id"] if i in self._i_idx]
            if len(session) >= 2:
                sessions.append(session)

        dataset = _SessionDataset(sessions, n_items, self.max_session_len)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True, collate_fn=_collate_sessions)

        device = torch.device(self.device)
        self._model = _GRU4Rec(n_items, self.embed_dim, self.hidden_dim, self.num_layers).to(device)
        optim = torch.optim.Adam(self._model.parameters(), lr=self.lr)

        self._model.train()
        for _ in range(self.epochs):
            total_loss = 0.0
            for x, lengths, y in loader:
                x, lengths, y = x.to(device), lengths.to(device), y.to(device)
                logits = self._model(x, lengths)
                loss = F.cross_entropy(logits, y)
                optim.zero_grad()
                loss.backward()
                optim.step()
                total_loss += loss.item()

    def recommend(
        self,
        user_id: int | str,
        k: int = 10,
        exclude_seen: bool = True,
    ) -> list[Recommendation]:
        return []

    def recommend_from_session(
        self,
        session_items: list[int | str],
        k: int = 10,
    ) -> list[Recommendation]:
        if self._model is None or self._item_ids is None:
            return []
        device = torch.device(self.device)
        indices = [self._i_idx.get(it, 0) for it in session_items]
        indices = [i for i in indices if i != 0]
        if not indices:
            return self._popular_fallback(k)
        if len(indices) > self.max_session_len:
            indices = indices[-self.max_session_len:]
        x = torch.tensor([indices], dtype=torch.long, device=device)
        lengths = torch.tensor([len(indices)], device=device)

        self._model.eval()
        with torch.no_grad():
            logits = self._model(x, lengths)
            scores = torch.softmax(logits, dim=-1).cpu().numpy().ravel()

        top = np.argsort(-scores)[:k]
        return [
            Recommendation(item_id=self._item_ids[i], score=float(scores[i]))
            for i in top
        ]

    def _popular_fallback(self, k: int) -> list[Recommendation]:
        if self._item_popularity is None or self._item_ids is None:
            return []
        top = np.argsort(-self._item_popularity)[:k]
        return [
            Recommendation(item_id=self._item_ids[i], score=float(self._item_popularity[i]))
            for i in top
        ]
