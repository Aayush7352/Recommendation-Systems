from __future__ import annotations

import time
from typing import Any

import mlflow

from .models.base import BaseRecommender


class ExperimentTracker:
    def __init__(self, experiment_name: str, tracking_uri: str | None = None):
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment_name)
        self.experiment_name = experiment_name

    def log_training(self, domain: str, model_name: str, model: BaseRecommender, params: dict[str, Any], metrics: dict[str, float] | None = None):
        with mlflow.start_run(run_name=f"{domain}/{model_name}") as run:
            mlflow.set_tag("domain", domain)
            mlflow.set_tag("model", model_name)
            mlflow.log_params(params)
            if metrics:
                mlflow.log_metrics(metrics)
            mlflow.log_text(str(model), "model_summary.txt")
            return run.info.run_id

    def log_evaluation(self, domain: str, k: int, metrics: dict[str, float], algo_metrics: dict[str, dict[str, float]] | None = None):
        with mlflow.start_run(run_name=f"eval/{domain}/@{k}") as run:
            mlflow.set_tag("domain", domain)
            mlflow.set_tag("run_type", "evaluation")
            mlflow.log_param("k", k)
            mlflow.log_metrics(metrics)
            if algo_metrics:
                for algo, m in algo_metrics.items():
                    mlflow.log_metrics({f"{algo}_{k}": v for k, v in m.items()})
            return run.info.run_id
