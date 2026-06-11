from __future__ import annotations

import csv
import io
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

MIND_SMALL_TRAIN_URL = "https://huggingface.co/datasets/Recommenders/MIND/resolve/main/MINDsmall_train.zip"
MIND_SMALL_DEV_URL = "https://huggingface.co/datasets/Recommenders/MIND/resolve/main/MINDsmall_dev.zip"
DEFAULT_CACHE = Path("data/raw/mind-small")

NEWS_COLS = [
    "news_id", "category", "subcategory", "title", "abstract",
    "url", "title_entities", "abstract_entities",
]
BEHAVIOR_COLS = ["impression_id", "user_id", "time", "history", "impressions"]


@dataclass
class MindData:
    news: pd.DataFrame
    behaviors_train: pd.DataFrame
    behaviors_dev: pd.DataFrame
    interactions: pd.DataFrame

    @property
    def n_users(self) -> int:
        return int(self.interactions["user_id"].nunique())

    @property
    def n_items(self) -> int:
        return int(self.news["news_id"].nunique())


def _download_and_extract(url: str, dest: Path, label: str) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    sentinel = dest / "behaviors.tsv"
    if sentinel.exists():
        return
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))
    buf = io.BytesIO()
    with tqdm(total=total, unit="B", unit_scale=True, desc=f"Downloading MIND-small/{label}") as bar:
        for chunk in resp.iter_content(chunk_size=8192):
            buf.write(chunk)
            bar.update(len(chunk))
    buf.seek(0)
    with zipfile.ZipFile(buf) as zf:
        zf.extractall(dest)


def _parse_news(path: Path) -> pd.DataFrame:
    df = pd.read_csv(
        path, sep="\t", header=None, names=NEWS_COLS,
        quoting=csv.QUOTE_NONE,
        na_filter=False,
        engine="c",
    )
    df["title_entities"] = df["title_entities"].apply(lambda s: json.loads(s) if s else [])
    df["abstract_entities"] = df["abstract_entities"].apply(lambda s: json.loads(s) if s else [])
    return df


def _parse_behaviors(path: Path) -> pd.DataFrame:
    df = pd.read_csv(
        path, sep="\t", header=None, names=BEHAVIOR_COLS,
        quoting=csv.QUOTE_NONE,
        na_filter=False,
        engine="c",
    )
    df["time"] = pd.to_datetime(df["time"], format="%m/%d/%Y %I:%M:%S %p")
    df["history"] = df["history"].apply(lambda s: s.split(" ") if s else [])
    return df


def _explode_clicks(behaviors: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in behaviors.itertuples(index=False):
        ts = row.time
        uid = row.user_id
        for hist_nid in row.history:
            rows.append((uid, hist_nid, 1, ts))
        for tok in row.impressions.split(" "):
            if not tok:
                continue
            nid, label = tok.rsplit("-", 1)
            if label == "1":
                rows.append((uid, nid, 1, ts))
    return pd.DataFrame(rows, columns=["user_id", "item_id", "rating", "timestamp"])


def load_mind_small(cache_dir: str | Path = DEFAULT_CACHE) -> MindData:
    cache = Path(cache_dir)
    train_dir = cache / "train"
    dev_dir = cache / "dev"
    _download_and_extract(MIND_SMALL_TRAIN_URL, train_dir, "train")
    _download_and_extract(MIND_SMALL_DEV_URL, dev_dir, "dev")

    news_train = _parse_news(train_dir / "news.tsv")
    news_dev = _parse_news(dev_dir / "news.tsv")
    news = pd.concat([news_train, news_dev], ignore_index=True).drop_duplicates(
        subset=["news_id"], keep="first"
    ).reset_index(drop=True)

    behaviors_train = _parse_behaviors(train_dir / "behaviors.tsv")
    behaviors_dev = _parse_behaviors(dev_dir / "behaviors.tsv")

    interactions = _explode_clicks(behaviors_train).drop_duplicates(
        subset=["user_id", "item_id"], keep="first"
    ).reset_index(drop=True)

    return MindData(
        news=news,
        behaviors_train=behaviors_train,
        behaviors_dev=behaviors_dev,
        interactions=interactions,
    )
