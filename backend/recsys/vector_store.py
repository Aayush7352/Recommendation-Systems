from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm
from qdrant_client.http.exceptions import UnexpectedResponse

from .models.base import Recommendation

COLLECTION_DENSE = "item_vectors"
COLLECTION_SPARSE = "cold_start_items"


class VectorStore:
    def __init__(self, host: str = "localhost", port: int = 6333, path: str | None = None):
        if path:
            self.client = QdrantClient(path=path)
        else:
            self.client = QdrantClient(host=host, port=port)
        self._collection_cache: set[str] = set()

    def _ensure_collection(self, name: str, dim: int):
        if name in self._collection_cache:
            return
        try:
            self.client.get_collection(name)
        except (UnexpectedResponse, ValueError):
            self.client.create_collection(
                collection_name=name,
                vectors_config=qm.VectorParams(size=dim, distance=qm.Distance.COSINE),
            )
        self._collection_cache.add(name)

    def index_item_vectors(self, item_ids: np.ndarray, vectors: np.ndarray, payloads: list[dict] | None = None):
        dim = vectors.shape[1]
        self._ensure_collection(COLLECTION_DENSE, dim)
        points = [
            qm.PointStruct(id=int(i), vector=v.tolist(), payload=payloads[i] if payloads else {})
            for i, v in enumerate(vectors)
        ]
        for batch_start in range(0, len(points), 256):
            batch = points[batch_start : batch_start + 256]
            self.client.upsert(COLLECTION_DENSE, batch)

    def search(self, vector: np.ndarray, k: int = 10, offset: int = 0) -> list[Recommendation]:
        results = self.client.search(
            collection_name=COLLECTION_DENSE,
            query_vector=vector.tolist(),
            limit=k,
            offset=offset,
        )
        return [
            Recommendation(item_id=res.id, score=float(res.score))
            for res in results
        ]

    def index_cold_start_items(self, items: pd.DataFrame, text_features: np.ndarray):
        dim = text_features.shape[1]
        self._ensure_collection(COLLECTION_SPARSE, dim)
        points = [
            qm.PointStruct(
                id=int(i),
                vector=text_features[i].tolist(),
                payload={
                    "item_id": str(row["item_id"]),
                    "title": row.get("title", ""),
                    "metadata": {
                        k: str(v) for k, v in row.items()
                        if k not in ("item_id", "title")
                    },
                },
            )
            for i, (_, row) in enumerate(items.iterrows())
        ]
        for batch_start in range(0, len(points), 256):
            batch = points[batch_start : batch_start + 256]
            self.client.upsert(COLLECTION_SPARSE, batch)

    def cold_start_search(self, text_vector: np.ndarray, k: int = 10) -> list[Recommendation]:
        results = self.client.search(
            collection_name=COLLECTION_SPARSE,
            query_vector=text_vector.tolist(),
            limit=k,
        )
        return [
            Recommendation(item_id=res.payload["item_id"], score=float(res.score))
            for res in results
        ]

    def close(self):
        self.client.close()
