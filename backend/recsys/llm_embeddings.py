from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class LLMEmbeddings:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name, device=self.device)

    def encode_items(
        self,
        items: pd.DataFrame,
        text_cols: list[str] | None = None,
        batch_size: int = 64,
    ) -> dict[str, Any]:
        self._load()
        cols = text_cols or [c for c in items.columns if items[c].dtype == "object" and c != "item_id"]
        texts = []
        item_ids = items["item_id"].tolist()
        for _, row in items.iterrows():
            parts = [str(row[c]).strip() for c in cols if c in items.columns and pd.notna(row[c])]
            texts.append(" ".join(parts) if parts else "unknown")
        embeddings = self._model.encode(texts, batch_size=batch_size, show_progress_bar=False)
        return {
            "item_ids": np.array(item_ids),
            "embeddings": embeddings.astype(np.float32),
        }

    def encode_text(self, text: str) -> np.ndarray:
        self._load()
        return self._model.encode([text], show_progress_bar=False)[0].astype(np.float32)

    def compute_similarity(self, emb_a: np.ndarray, emb_b: np.ndarray) -> float:
        a = emb_a / np.linalg.norm(emb_a)
        b = emb_b / np.linalg.norm(emb_b)
        return float(np.dot(a, b))
