from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any

import pandas as pd

from .models.base import BaseRecommender, Recommendation


class ABTestFramework:
    def __init__(self, assignment_log: str = "data/ab_assignments.jsonl"):
        self.assignment_log = Path(assignment_log)
        self.assignment_log.parent.mkdir(parents=True, exist_ok=True)

    def assign_variant(self, user_id: int | str, a_name: str, b_name: str, split: float = 0.5) -> str:
        seed = int(hashlib.md5(str(user_id).encode()).hexdigest()[:8], 16) % 1000
        variant = a_name if (seed / 1000) < split else b_name
        with self.assignment_log.open("a") as f:
            f.write(json.dumps({"user_id": user_id, "variant": variant}) + "\n")
        return variant

    def evaluate(
        self,
        user_id: int | str,
        model_a: BaseRecommender,
        model_b: BaseRecommender,
        interactions: pd.DataFrame,
        k: int = 10,
    ) -> dict[str, Any]:
        recs_a = model_a.recommend(user_id, k=k, exclude_seen=True)
        recs_b = model_b.recommend(user_id, k=k, exclude_seen=True)
        return {
            "user_id": user_id,
            "model_a": self._summarize(user_id, recs_a, interactions),
            "model_b": self._summarize(user_id, recs_b, interactions),
        }

    def _summarize(
        self,
        user_id: int | str,
        recs: list[Recommendation],
        interactions: pd.DataFrame,
    ) -> dict[str, Any]:
        user_items = set(interactions[interactions["user_id"] == user_id]["item_id"])
        seen_in_recs = sum(1 for r in recs if r.item_id in user_items)
        return {
            "n_recs": len(recs),
            "avg_score": float(sum(r.score for r in recs) / len(recs)) if recs else 0,
            "seen_in_recs": seen_in_recs,
            "novel_items": len(recs) - seen_in_recs,
        }

    def compare_results(self, results_a: list, results_b: list) -> dict[str, Any]:
        avg_score_a = sum(r["model_a"]["avg_score"] for r in results_a) / len(results_a) if results_a else 0
        avg_score_b = sum(r["model_b"]["avg_score"] for r in results_b) / len(results_b) if results_b else 0
        novelty_a = sum(r["model_a"]["novel_items"] for r in results_a) / len(results_a) if results_a else 0
        novelty_b = sum(r["model_b"]["novel_items"] for r in results_b) / len(results_b) if results_b else 0
        return {
            "model_a": {
                "avg_score": round(avg_score_a, 4),
                "avg_novelty": round(novelty_a, 2),
            },
            "model_b": {
                "avg_score": round(avg_score_b, 4),
                "avg_novelty": round(novelty_b, 2),
            },
            "winner": "a" if avg_score_a > avg_score_b else "b",
        }
