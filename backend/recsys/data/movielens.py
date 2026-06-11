from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

ML100K_URL = "https://files.grouplens.org/datasets/movielens/ml-100k.zip"
DEFAULT_CACHE = Path("data/raw/ml-100k")

GENRE_COLS = [
    "unknown", "Action", "Adventure", "Animation", "Children", "Comedy",
    "Crime", "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror",
    "Musical", "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western",
]


@dataclass
class MovieLensData:
    ratings: pd.DataFrame
    items: pd.DataFrame
    users: pd.DataFrame

    @property
    def n_users(self) -> int:
        return int(self.ratings["user_id"].nunique())

    @property
    def n_items(self) -> int:
        return int(self.items["item_id"].nunique())


def _download(cache_dir: Path) -> None:
    cache_dir.parent.mkdir(parents=True, exist_ok=True)
    if cache_dir.exists() and (cache_dir / "u.data").exists():
        return
    resp = requests.get(ML100K_URL, stream=True, timeout=60)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))
    buf = io.BytesIO()
    with tqdm(total=total, unit="B", unit_scale=True, desc="Downloading MovieLens-100K") as bar:
        for chunk in resp.iter_content(chunk_size=8192):
            buf.write(chunk)
            bar.update(len(chunk))
    buf.seek(0)
    with zipfile.ZipFile(buf) as zf:
        zf.extractall(cache_dir.parent)


def load_movielens_100k(cache_dir: str | Path = DEFAULT_CACHE) -> MovieLensData:
    cache = Path(cache_dir)
    _download(cache)

    ratings = pd.read_csv(
        cache / "u.data",
        sep="\t",
        names=["user_id", "item_id", "rating", "timestamp"],
        engine="c",
    )

    item_cols = ["item_id", "title", "release_date", "video_release", "imdb_url", *GENRE_COLS]
    items_raw = pd.read_csv(
        cache / "u.item",
        sep="|",
        names=item_cols,
        encoding="latin-1",
        engine="c",
    )
    genres = items_raw[GENRE_COLS].apply(
        lambda row: [g for g, v in row.items() if v == 1], axis=1
    )
    items = pd.DataFrame({
        "item_id": items_raw["item_id"],
        "title": items_raw["title"],
        "release_date": items_raw["release_date"],
        "genres": genres,
    })

    users = pd.read_csv(
        cache / "u.user",
        sep="|",
        names=["user_id", "age", "gender", "occupation", "zip"],
        engine="c",
    )

    return MovieLensData(ratings=ratings, items=items, users=users)
