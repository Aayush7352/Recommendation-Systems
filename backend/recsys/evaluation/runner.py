from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import pandas as pd

from ..models.base import BaseRecommender
from .metrics import EvalReport, evaluate
from .split import leave_one_out_split


@dataclass
class DomainEvalResult:
    domain: str
    k: int
    n_users: int
    n_items: int
    reports: list[EvalReport]

    def as_dict(self) -> dict:
        return {
            "domain": self.domain,
            "k": self.k,
            "n_users": self.n_users,
            "n_items": self.n_items,
            "reports": [r.as_dict() for r in self.reports],
        }


def evaluate_models(
    domain: str,
    models: dict[str, BaseRecommender],
    interactions: pd.DataFrame,
    items: pd.DataFrame | None = None,
    users: pd.DataFrame | None = None,
    k: int = 10,
    max_eval_users: int | None = 500,
    seed: int = 42,
) -> DomainEvalResult:
    split = leave_one_out_split(interactions, seed=seed)
    train, test = split.train, split.test

    ground_truth: dict = {}
    for _, row in test.iterrows():
        ground_truth.setdefault(row["user_id"], set()).add(row["item_id"])

    eval_users = list(ground_truth.keys())
    if max_eval_users and len(eval_users) > max_eval_users:
        import random
        rng = random.Random(seed)
        eval_users = rng.sample(eval_users, max_eval_users)

    item_pop = Counter(train["item_id"])
    n_items = int(pd.concat([train["item_id"], test["item_id"]]).nunique())

    reports: list[EvalReport] = []
    for name, model in models.items():
        model.fit(train, items=items, users=users)
        recs = model.recommend_batch(eval_users, k=k)
        report = evaluate(
            recommendations=recs,
            ground_truth={u: ground_truth[u] for u in eval_users},
            k=k,
            n_items=n_items,
            item_popularity=item_pop,
            algo_name=name,
        )
        reports.append(report)

    return DomainEvalResult(
        domain=domain,
        k=k,
        n_users=int(interactions["user_id"].nunique()),
        n_items=n_items,
        reports=reports,
    )
