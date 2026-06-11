from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class Recommendation:
    item_id: int | str
    score: float


class BaseRecommender(ABC):
    name: str = "base"

    @abstractmethod
    def fit(
        self,
        interactions: pd.DataFrame,
        items: pd.DataFrame | None = None,
        users: pd.DataFrame | None = None,
    ) -> None: ...

    @abstractmethod
    def recommend(
        self,
        user_id: int | str,
        k: int = 10,
        exclude_seen: bool = True,
    ) -> list[Recommendation]: ...

    def recommend_batch(
        self,
        user_ids: list[int | str],
        k: int = 10,
        exclude_seen: bool = True,
    ) -> dict[int | str, list[Recommendation]]:
        return {uid: self.recommend(uid, k=k, exclude_seen=exclude_seen) for uid in user_ids}


@dataclass
class TrainTestSplit:
    train: pd.DataFrame
    test: pd.DataFrame
    n_users: int = field(init=False)
    n_items: int = field(init=False)

    def __post_init__(self) -> None:
        all_users = pd.concat([self.train["user_id"], self.test["user_id"]]).unique()
        all_items = pd.concat([self.train["item_id"], self.test["item_id"]]).unique()
        self.n_users = len(all_users)
        self.n_items = len(all_items)
