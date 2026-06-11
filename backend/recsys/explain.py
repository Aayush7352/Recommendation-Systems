from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .models.base import BaseRecommender, Recommendation


class Explainer:
    def explain_recommendation(
        self,
        model: BaseRecommender,
        user_id: int | str,
        rec: Recommendation,
        interactions: pd.DataFrame,
        items: pd.DataFrame | None = None,
        k: int = 10,
    ) -> dict[str, Any]:
        user_items = interactions[interactions["user_id"] == user_id]["item_id"].tolist()
        explanation: dict[str, Any] = {
            "user_id": user_id,
            "recommended_item": rec.item_id,
            "score": rec.score,
            "reason": self._generate_reason(model, user_id, rec, user_items, items),
            "user_history_count": len(user_items),
            "similar_users_count": self._count_similar_users(user_id, interactions),
        }
        return explanation

    def _generate_reason(
        self,
        model: BaseRecommender,
        user_id: int | str,
        rec: Recommendation,
        user_items: list,
        items: pd.DataFrame | None = None,
    ) -> str:
        model_name = getattr(model, "name", "unknown")

        if model_name == "popularity":
            return "This item is popular among all users."
        if model_name == "content_based":
            return "This item matches your preferred content categories."
        if model_name == "item_knn":
            return f"Similar to items you have interacted with before."
        if model_name == "als":
            return "Users with similar tastes also liked this item."
        if model_name == "hybrid":
            return "Recommended based on your preferences and similar users."
        if model_name == "two_tower":
            return "Our neural network found this highly relevant to your interests."
        if model_name == "gru4rec":
            return "Based on your current session, you might enjoy this next."
        return "Recommended for you."

    def _count_similar_users(self, user_id: int | str, interactions: pd.DataFrame) -> int:
        user_items = set(interactions[interactions["user_id"] == user_id]["item_id"])
        if len(user_items) < 2:
            return 0
        other_users = interactions[interactions["item_id"].isin(user_items)]["user_id"].unique()
        return max(0, len(other_users) - 1)

    def feature_importance(
        self,
        model: BaseRecommender,
        user_id: int | str,
        interactions: pd.DataFrame,
        items: pd.DataFrame | None = None,
    ) -> dict[str, float]:
        features: dict[str, float] = {
            "user_history_length": 0.0,
            "item_popularity": 0.0,
            "content_similarity": 0.0,
            "collaborative_signal": 0.0,
        }
        user_items = interactions[interactions["user_id"] == user_id]
        features["user_history_length"] = min(1.0, len(user_items) / 100.0)
        if len(user_items) > 0:
            avg_rating = user_items["rating"].mean() if "rating" in user_items.columns else 3.0
            features["content_similarity"] = avg_rating / 5.0
        model_name = getattr(model, "name", "unknown")
        if model_name in ("als", "item_knn", "hybrid", "two_tower"):
            features["collaborative_signal"] = 0.8
        if model_name in ("popularity",):
            features["item_popularity"] = 1.0
        if model_name in ("content_based",):
            features["content_similarity"] = 0.9
        if model_name in ("hybrid",):
            features["content_similarity"] = 0.5
            features["collaborative_signal"] = 0.5
        total = sum(features.values()) or 1.0
        return {k: round(v / total, 4) for k, v in features.items()}
