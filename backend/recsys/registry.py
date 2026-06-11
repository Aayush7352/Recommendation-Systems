from __future__ import annotations

import pickle
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .data.mind import MindData, load_mind_small
from .data.movielens import MovieLensData, load_movielens_100k
from .models.base import BaseRecommender
from .models.collaborative import ALSRecommender, ItemKNNRecommender
from .models.content_based import ContentBasedRecommender
from .models.hybrid import HybridRecommender
from .models.popularity import PopularityRecommender
from .models.two_tower import TwoTowerRecommender

ARTIFACT_DIR = Path("data/artifacts")
DOMAINS = ("movies", "news")


@dataclass
class DomainBundle:
    domain: str
    interactions: pd.DataFrame
    items: pd.DataFrame
    users: pd.DataFrame | None
    models: dict[str, BaseRecommender] = field(default_factory=dict)


def _build_movie_models() -> dict[str, BaseRecommender]:
    cb = ContentBasedRecommender(tags_col="genres", min_rating_for_profile=4.0)
    als = ALSRecommender(factors=64, iterations=20)
    return {
        "popularity": PopularityRecommender(),
        "content_based": cb,
        "item_knn": ItemKNNRecommender(k_neighbors=50),
        "als": als,
        "hybrid": HybridRecommender(components=[
            (ContentBasedRecommender(tags_col="genres", min_rating_for_profile=4.0), 0.4),
            (ALSRecommender(factors=64, iterations=20), 0.6),
        ]),
        "two_tower": TwoTowerRecommender(
            embed_dim=32, mlp_dims=(64, 32), epochs=8, batch_size=512, genre_col="genres",
        ),
    }


def _build_news_models() -> dict[str, BaseRecommender]:
    return {
        "popularity": PopularityRecommender(),
        "content_based": ContentBasedRecommender(
            text_cols=["title", "abstract"],
            tags_col=None,
            min_rating_for_profile=1.0,
        ),
        "item_knn": ItemKNNRecommender(k_neighbors=50),
        "als": ALSRecommender(factors=64, iterations=15),
        "hybrid": HybridRecommender(components=[
            (ContentBasedRecommender(text_cols=["title", "abstract"], min_rating_for_profile=1.0), 0.5),
            (ALSRecommender(factors=64, iterations=15), 0.5),
        ]),
        "two_tower": TwoTowerRecommender(
            embed_dim=32, mlp_dims=(64, 32), epochs=5, batch_size=1024,
        ),
    }


def _prepare_news_interactions(mind: MindData, max_users: int = 5000) -> pd.DataFrame:
    user_counts = mind.interactions.groupby("user_id").size().sort_values(ascending=False)
    top_users = user_counts.head(max_users).index
    return mind.interactions[mind.interactions["user_id"].isin(top_users)].reset_index(drop=True)


def _prepare_news_items(mind: MindData, interactions: pd.DataFrame) -> pd.DataFrame:
    active_items = set(interactions["item_id"])
    items = mind.news[mind.news["news_id"].isin(active_items)].copy()
    items = items.rename(columns={"news_id": "item_id"})
    return items.reset_index(drop=True)


def load_movie_bundle() -> DomainBundle:
    data: MovieLensData = load_movielens_100k()
    return DomainBundle(
        domain="movies",
        interactions=data.ratings,
        items=data.items,
        users=data.users,
    )


def load_news_bundle(max_users: int = 5000) -> DomainBundle:
    data: MindData = load_mind_small()
    interactions = _prepare_news_interactions(data, max_users=max_users)
    items = _prepare_news_items(data, interactions)
    return DomainBundle(
        domain="news",
        interactions=interactions,
        items=items,
        users=None,
    )


def train_domain(bundle: DomainBundle) -> DomainBundle:
    builders = {"movies": _build_movie_models, "news": _build_news_models}
    models = builders[bundle.domain]()
    for name, m in models.items():
        m.fit(bundle.interactions, items=bundle.items, users=bundle.users)
        bundle.models[name] = m
    return bundle


def artifact_path(domain: str) -> Path:
    return ARTIFACT_DIR / f"{domain}.pkl"


def save_bundle(bundle: DomainBundle) -> Path:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    path = artifact_path(bundle.domain)
    with path.open("wb") as f:
        pickle.dump(bundle, f)
    return path


def load_bundle(domain: str) -> DomainBundle:
    path = artifact_path(domain)
    if not path.exists():
        raise FileNotFoundError(
            f"No trained bundle at {path}. Run `python -m recsys.cli train` first."
        )
    with path.open("rb") as f:
        return pickle.load(f)
