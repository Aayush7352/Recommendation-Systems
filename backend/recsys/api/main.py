from __future__ import annotations

import json
import time
from functools import lru_cache
from pathlib import Path

import structlog
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = structlog.get_logger()

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from ..ab_testing import ABTestFramework
from ..evaluation.runner import evaluate_models
from ..explain import Explainer
from ..models.cold_start import ColdStartRecommender
from ..monitoring import DriftDetector

REQUEST_COUNT = Counter("recsys_requests_total", "Total requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("recsys_request_latency_seconds", "Request latency", ["method", "path"])
RECOMMENDATIONS_COUNT = Counter("recsys_recommendations_total", "Total recommendations served", ["domain", "algo"])
from ..registry import (
    DOMAINS,
    DomainBundle,
    _build_movie_models,
    _build_news_models,
    artifact_path,
    load_bundle,
)

EVAL_CACHE_DIR = Path("data/artifacts/eval")
drift_detector = DriftDetector()
ab_framework = ABTestFramework()
explainer = Explainer()

app = FastAPI(title="RecSys Lab", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    t0 = time.time()
    response = await call_next(request)
    elapsed = time.time() - t0
    REQUEST_COUNT.labels(method=request.method, path=request.url.path, status=response.status_code).inc()
    REQUEST_LATENCY.labels(method=request.method, path=request.url.path).observe(elapsed)
    logger.info(
        "request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        elapsed_ms=round(elapsed * 1000),
    )
    return response


@app.get("/metrics")
def metrics():
    return JSONResponse(content=generate_latest().decode(), media_type=CONTENT_TYPE_LATEST)


class RecItem(BaseModel):
    item_id: int | str
    score: float
    title: str | None = None
    metadata: dict | None = None


class RecResponse(BaseModel):
    domain: str
    algo: str
    user_id: int | str
    items: list[RecItem]


class UserSummary(BaseModel):
    user_id: int | str
    n_interactions: int


class ItemSummary(BaseModel):
    item_id: int | str
    title: str | None = None
    metadata: dict | None = None


@lru_cache(maxsize=4)
def _bundle(domain: str) -> DomainBundle:
    if domain not in DOMAINS:
        raise HTTPException(status_code=404, detail=f"unknown domain '{domain}'")
    try:
        return load_bundle(domain)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


def _item_lookup(bundle: DomainBundle) -> dict:
    items = bundle.items
    if bundle.domain == "movies":
        return {
            row["item_id"]: {
                "title": row["title"],
                "metadata": {
                    "genres": row["genres"],
                    "release_date": row.get("release_date"),
                },
            }
            for _, row in items.iterrows()
        }
    return {
        row["item_id"]: {
            "title": row["title"],
            "metadata": {
                "category": row["category"],
                "subcategory": row["subcategory"],
                "abstract": row["abstract"][:200] if isinstance(row["abstract"], str) else "",
            },
        }
        for _, row in items.iterrows()
    }


@lru_cache(maxsize=4)
def _item_lookup_cached(domain: str) -> dict:
    return _item_lookup(_bundle(domain))


@app.get("/")
def root() -> dict:
    return {
        "service": "recsys-lab",
        "domains": list(DOMAINS),
        "loaded": {d: artifact_path(d).exists() for d in DOMAINS},
    }


@app.get("/domains/{domain}/info")
def domain_info(domain: str) -> dict:
    b = _bundle(domain)
    return {
        "domain": domain,
        "n_users": int(b.interactions["user_id"].nunique()),
        "n_items": int(b.items["item_id"].nunique()),
        "n_interactions": int(len(b.interactions)),
        "algos": list(b.models.keys()),
    }


@app.get("/domains/{domain}/users", response_model=list[UserSummary])
def list_users(domain: str, limit: int = Query(50, ge=1, le=500)) -> list[UserSummary]:
    b = _bundle(domain)
    counts = b.interactions.groupby("user_id").size().sort_values(ascending=False).head(limit)
    return [UserSummary(user_id=u, n_interactions=int(c)) for u, c in counts.items()]


@app.get("/domains/{domain}/users/{user_id}/history", response_model=list[ItemSummary])
def user_history(
    domain: str,
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
) -> list[ItemSummary]:
    b = _bundle(domain)
    uid: int | str
    try:
        uid = int(user_id)
    except ValueError:
        uid = user_id
    hist = b.interactions[b.interactions["user_id"] == uid]
    if "timestamp" in hist.columns:
        ts = hist["timestamp"].values.astype("int64")
        hist = hist.iloc[ts.argsort()[::-1]]
    hist = hist.head(limit)
    lookup = _item_lookup_cached(domain)
    out: list[ItemSummary] = []
    for iid in hist["item_id"]:
        meta = lookup.get(iid, {})
        out.append(ItemSummary(item_id=iid, title=meta.get("title"), metadata=meta.get("metadata")))
    return out


@app.get("/domains/{domain}/items", response_model=list[ItemSummary])
def list_items(domain: str, limit: int = Query(50, ge=1, le=500)) -> list[ItemSummary]:
    b = _bundle(domain)
    lookup = _item_lookup_cached(domain)
    out: list[ItemSummary] = []
    for iid in b.items["item_id"].head(limit):
        meta = lookup.get(iid, {})
        out.append(ItemSummary(item_id=iid, title=meta.get("title"), metadata=meta.get("metadata")))
    return out


@app.get("/recommend/{domain}/compare/{user_id}")
def recommend_compare(
    domain: str,
    user_id: str,
    algos: str | None = Query(None, description="Comma-separated algo names; default: all"),
    k: int = Query(10, ge=1, le=50),
) -> dict:
    b = _bundle(domain)
    selected = [a.strip() for a in algos.split(",")] if algos else list(b.models.keys())
    uid: int | str
    try:
        uid = int(user_id)
    except ValueError:
        uid = user_id
    lookup = _item_lookup_cached(domain)
    out: dict = {"domain": domain, "user_id": uid, "k": k, "results": {}}
    for a in selected:
        if a not in b.models:
            continue
        recs = b.models[a].recommend(uid, k=k, exclude_seen=True)
        out["results"][a] = [
            {
                "item_id": int(r.item_id) if not isinstance(r.item_id, (int, str)) else r.item_id,
                "score": float(r.score),
                "title": lookup.get(r.item_id, {}).get("title"),
                "metadata": lookup.get(r.item_id, {}).get("metadata"),
            }
            for r in recs
        ]
    return out


@app.get("/recommend/{domain}/{algo}/{user_id}", response_model=RecResponse)
def recommend(
    domain: str,
    algo: str,
    user_id: str,
    k: int = Query(10, ge=1, le=100),
) -> RecResponse:
    b = _bundle(domain)
    if algo not in b.models:
        raise HTTPException(status_code=404, detail=f"unknown algo '{algo}' for {domain}")
    uid: int | str
    try:
        uid = int(user_id)
    except ValueError:
        uid = user_id
    recs = b.models[algo].recommend(uid, k=k, exclude_seen=True)
    lookup = _item_lookup_cached(domain)
    items = [
        RecItem(
            item_id=r.item_id,
            score=r.score,
            title=lookup.get(r.item_id, {}).get("title"),
            metadata=lookup.get(r.item_id, {}).get("metadata"),
        )
        for r in recs
    ]
    return RecResponse(domain=domain, algo=algo, user_id=uid, items=items)


@app.get("/search/{domain}")
def search_items(domain: str, q: str = Query(..., min_length=1), k: int = Query(10, ge=1, le=50)) -> list[ItemSummary]:
    if domain not in DOMAINS:
        raise HTTPException(status_code=404, detail=f"unknown domain '{domain}'")
    b = _bundle(domain)
    cs = ColdStartRecommender(
        text_cols=["title", "genres"] if domain == "movies" else ["title", "abstract", "category"],
    )
    try:
        cs.fit(b.interactions, items=b.items, users=b.users)
    except Exception:
        cs.fit(b.interactions, items=b.items)
    recs = cs.recommend_from_text(q, k=k)
    lookup = _item_lookup_cached(domain)
    return [
        ItemSummary(
            item_id=r.item_id,
            title=lookup.get(r.item_id, {}).get("title"),
            metadata=lookup.get(r.item_id, {}).get("metadata"),
        )
        for r in recs
    ]


@app.get("/monitor/drift/{domain}")
def get_drift_report(domain: str) -> dict:
    if domain not in DOMAINS:
        raise HTTPException(status_code=404, detail=f"unknown domain '{domain}'")
    b = _bundle(domain)
    report = drift_detector.check_data_drift(
        reference=b.interactions,
        current=b.interactions.sample(frac=0.3, random_state=42),
        domain=domain,
    )
    return report


@app.get("/monitor/drift/{domain}/{model_name}")
def get_model_drift(domain: str, model_name: str) -> dict:
    if domain not in DOMAINS:
        raise HTTPException(status_code=404, detail=f"unknown domain '{domain}'")
    b = _bundle(domain)
    if model_name not in b.models:
        raise HTTPException(status_code=404, detail=f"unknown model '{model_name}'")
    report = drift_detector.check_model_drift(
        model=b.models[model_name],
        reference_interactions=b.interactions,
        current_interactions=b.interactions.sample(frac=0.3, random_state=42),
        domain=domain,
        model_name=model_name,
    )
    return report


@app.get("/recommend/{domain}/session/{user_id}")
def recommend_session(
    domain: str,
    user_id: str,
    session_items: str = Query(..., description="Comma-separated item IDs from current session"),
    k: int = Query(10, ge=1, le=50),
) -> dict:
    if domain not in DOMAINS:
        raise HTTPException(status_code=404, detail=f"unknown domain '{domain}'")
    b = _bundle(domain)
    model = b.models.get("gru4rec")
    if model is None:
        raise HTTPException(status_code=503, detail="GRU4Rec model not trained")
    items = [s.strip() for s in session_items.split(",")]
    uid: int | str
    try:
        uid = int(user_id)
    except ValueError:
        uid = user_id
    try:
        uid_int = int(uid) if isinstance(uid, str) and uid.isdigit() else uid
        recs = model.recommend_from_session(items, k=k)
    except Exception:
        recs = []
    lookup = _item_lookup_cached(domain)
    return {
        "domain": domain,
        "user_id": uid,
        "session_items": items,
        "items": [
            {"item_id": r.item_id, "score": r.score, "title": lookup.get(r.item_id, {}).get("title")}
            for r in recs
        ],
    }


@app.get("/explain/{domain}/{algo}/{user_id}")
def explain_recommendation(
    domain: str,
    algo: str,
    user_id: str,
    item_id: str = Query(..., description="Item ID to explain"),
) -> dict:
    if domain not in DOMAINS:
        raise HTTPException(status_code=404, detail=f"unknown domain '{domain}'")
    b = _bundle(domain)
    if algo not in b.models:
        raise HTTPException(status_code=404, detail=f"unknown algo '{algo}'")
    uid: int | str
    try:
        uid = int(user_id)
    except ValueError:
        uid = user_id
    try:
        iid = int(item_id)
    except ValueError:
        iid = item_id
    lookup = _item_lookup_cached(domain)
    recs = b.models[algo].recommend(uid, k=50, exclude_seen=True)
    rec = next((r for r in recs if r.item_id == iid), None)
    if rec is None:
        raise HTTPException(status_code=404, detail="Item not in recommendations")
    explanation = explainer.explain_recommendation(
        b.models[algo], uid, rec, b.interactions, b.items
    )
    explanation["title"] = lookup.get(iid, {}).get("title")
    return explanation


@app.get("/explain/{domain}/{algo}/{user_id}/features")
def feature_importance(
    domain: str,
    algo: str,
    user_id: str,
) -> dict:
    if domain not in DOMAINS:
        raise HTTPException(status_code=404, detail=f"unknown domain '{domain}'")
    b = _bundle(domain)
    if algo not in b.models:
        raise HTTPException(status_code=404, detail=f"unknown algo '{algo}'")
    uid: int | str
    try:
        uid = int(user_id)
    except ValueError:
        uid = user_id
    importance = explainer.feature_importance(b.models[algo], uid, b.interactions, b.items)
    return {"domain": domain, "algo": algo, "user_id": uid, "feature_importance": importance}


@app.get("/ab-test/{domain}/{user_id}")
def ab_test(
    domain: str,
    user_id: str,
    model_a: str = Query("popularity"),
    model_b: str = Query("als"),
    k: int = Query(10, ge=1, le=50),
) -> dict:
    if domain not in DOMAINS:
        raise HTTPException(status_code=404, detail=f"unknown domain '{domain}'")
    b = _bundle(domain)
    if model_a not in b.models or model_b not in b.models:
        raise HTTPException(status_code=404, detail="unknown model")
    variant = ab_framework.assign_variant(user_id, model_a, model_b)
    chosen = model_a if variant == model_a else model_b
    uid: int | str
    try:
        uid = int(user_id)
    except ValueError:
        uid = user_id
    recs = b.models[chosen].recommend(uid, k=k, exclude_seen=True)
    lookup = _item_lookup_cached(domain)
    return {
        "domain": domain,
        "user_id": user_id,
        "variant": variant,
        "items": [
            {
                "item_id": r.item_id,
                "score": r.score,
                "title": lookup.get(r.item_id, {}).get("title"),
            }
            for r in recs
        ],
    }


@app.get("/evaluate/{domain}")
def get_evaluation(domain: str, refresh: bool = False, k: int = 10) -> dict:
    if domain not in DOMAINS:
        raise HTTPException(status_code=404, detail=f"unknown domain '{domain}'")
    EVAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = EVAL_CACHE_DIR / f"{domain}_k{k}.json"
    if cache_file.exists() and not refresh:
        with cache_file.open() as f:
            return json.load(f)

    b = _bundle(domain)
    builder = _build_movie_models if domain == "movies" else _build_news_models
    result = evaluate_models(
        domain=domain,
        models=builder(),
        interactions=b.interactions,
        items=b.items,
        users=b.users,
        k=k,
        max_eval_users=300,
    )
    payload = result.as_dict()
    with cache_file.open("w") as f:
        json.dump(payload, f, indent=2)
    return payload
