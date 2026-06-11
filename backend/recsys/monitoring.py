from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .models.base import BaseRecommender


class DriftDetector:
    def __init__(self, report_dir: str = "data/monitoring"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def check_data_drift(
        self,
        reference: pd.DataFrame,
        current: pd.DataFrame,
        domain: str,
        timestamp_col: str = "timestamp",
    ) -> dict[str, Any]:
        numeric_cols = reference.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = reference.select_dtypes(include=["object", "category"]).columns.tolist()

        report: dict[str, Any] = {"domain": domain, "drift_detected": False, "checks": []}
        for col in numeric_cols:
            if col not in current.columns:
                continue
            ref_stats = reference[col].describe()
            cur_stats = current[col].describe()
            ps = self._psi(reference[col].values, current[col].values, bins=10)
            report["checks"].append({
                "column": col,
                "type": "numeric",
                "psi": round(float(ps), 4),
                "drift": ps > 0.2,
                "ref_mean": round(float(ref_stats["mean"]), 4),
                "cur_mean": round(float(cur_stats["mean"]), 4),
            })
            if ps > 0.2:
                report["drift_detected"] = True

        for col in cat_cols:
            if col not in current.columns:
                continue
            ref_dist = reference[col].value_counts(normalize=True).to_dict()
            cur_dist = current[col].value_counts(normalize=True).to_dict()
            js = self._jensen_shannon(ref_dist, cur_dist)
            report["checks"].append({
                "column": col,
                "type": "categorical",
                "js_divergence": round(float(js), 4),
                "drift": js > 0.1,
                "ref_categories": len(ref_dist),
                "cur_categories": len(cur_dist),
            })
            if js > 0.1:
                report["drift_detected"] = True

        path = self.report_dir / f"{domain}_data_drift.json"
        with path.open("w") as f:
            json.dump(report, f, indent=2, default=str)
        return report

    def _psi(self, expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
        expected_perc = np.histogram(expected, bins=bins, range=(0, 1))[0] / len(expected) + 1e-6
        actual_perc = np.histogram(actual, bins=bins, range=(0, 1))[0] / len(actual) + 1e-6
        return np.sum((actual_perc - expected_perc) * np.log(actual_perc / expected_perc))

    def _jensen_shannon(self, p: dict, q: dict) -> float:
        all_keys = set(p) | set(q)
        p_arr = np.array([p.get(k, 0) for k in all_keys])
        q_arr = np.array([q.get(k, 0) for k in all_keys])
        m = 0.5 * (p_arr + q_arr)
        return 0.5 * (np.sum(p_arr * np.log((p_arr + 1e-10) / (m + 1e-10))) +
                      np.sum(q_arr * np.log((q_arr + 1e-10) / (m + 1e-10))))

    def check_model_drift(
        self,
        model: BaseRecommender,
        reference_interactions: pd.DataFrame,
        current_interactions: pd.DataFrame,
        domain: str,
        model_name: str,
        k: int = 10,
    ) -> dict[str, Any]:
        ref_users = reference_interactions["user_id"].unique()[:100]
        cur_users = current_interactions["user_id"].unique()[:100]

        ref_scores = [model.recommend(u, k=k)[0].score if model.recommend(u, k=k) else 0 for u in ref_users]
        cur_scores = [model.recommend(u, k=k)[0].score if model.recommend(u, k=k) else 0 for u in cur_users]

        ps = self._psi(np.array(ref_scores), np.array(cur_scores))
        report = {
            "domain": domain,
            "model": model_name,
            "score_drift_psi": round(float(ps), 4),
            "drift_detected": ps > 0.2,
            "ref_avg_score": round(float(np.mean(ref_scores)), 4),
            "cur_avg_score": round(float(np.mean(cur_scores)), 4),
        }
        path = self.report_dir / f"{domain}_{model_name}_model_drift.json"
        with path.open("w") as f:
            json.dump(report, f, indent=2)
        return report
