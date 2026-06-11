# RecSys Lab

A research harness for comparing recommendation algorithms across two domains:

- **Movies** — MovieLens-100K (943 users, 1,682 items, 100K ratings)
- **News** — Microsoft MIND-small (filtered to most active users)

Six algorithms are trained per domain and exposed via a FastAPI backend with a Next.js + Tailwind frontend for side-by-side comparison and offline evaluation.

## Algorithms

| Key | Name | Family |
|---|---|---|
| `popularity` | Global most-popular | Baseline |
| `content_based` | TF-IDF + tag features over user profile | Content |
| `item_knn` | Item–item cosine k-NN | Collaborative (memory) |
| `als` | Implicit ALS matrix factorization | Collaborative (model) |
| `hybrid` | Weighted blend: content + ALS | Hybrid |
| `two_tower` | PyTorch user/item towers, in-batch sampled softmax | Neural |

All implement the same `BaseRecommender` interface (`fit`, `recommend`, `recommend_batch`) in `backend/recsys/models/base.py`.

## Project layout

```
backend/
  recsys/
    data/          MovieLens + MIND loaders (download + parse)
    models/        Six recommender implementations
    evaluation/    Train/test split, metrics, batch runner
    api/           FastAPI app
    registry.py    Train all models + pickle to disk
    cli.py         `python -m recsys.cli train|evaluate`
  pyproject.toml
frontend/          Next.js 14 + Tailwind UI
data/              Cached raw datasets + trained model artifacts
```

## Quick start

### 1. Backend

```bash
python3 -m venv .venv
.venv/bin/pip install -e ./backend
```

Train every model for both domains (downloads ~85 MB of data, caches under `data/raw/`, writes pickles to `data/artifacts/`):

```bash
.venv/bin/python -m recsys.cli train
```

Train a single domain:

```bash
.venv/bin/python -m recsys.cli train --domains movies
```

Run offline evaluation (writes JSON to `--out` if provided):

```bash
.venv/bin/python -m recsys.cli evaluate --k 10 --out data/artifacts/eval.json
```

Boot the API:

```bash
.venv/bin/uvicorn recsys.api.main:app --reload --port 8000
```

Interactive docs at <http://localhost:8000/docs>.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Visits <http://localhost:3000>. The frontend reads `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Service info + which domains have trained artifacts |
| GET | `/domains/{domain}/info` | User/item/interaction counts |
| GET | `/domains/{domain}/users?limit=N` | Top-N users by interaction count |
| GET | `/domains/{domain}/users/{user_id}/history` | A user's past interactions |
| GET | `/domains/{domain}/items?limit=N` | Sample of items |
| GET | `/recommend/{domain}/{algo}/{user_id}?k=N` | Top-K recs from one algo |
| GET | `/recommend/{domain}/compare/{user_id}?algos=a,b,c&k=N` | Side-by-side across algos |
| GET | `/evaluate/{domain}?k=N&refresh=bool` | Offline metrics report (cached) |

`{domain}` is `movies` or `news`. `{algo}` is one of `popularity, content_based, item_knn, als, hybrid, two_tower`.

## Evaluation protocol

- **Split**: leave-one-out per user. The last interaction (by timestamp) is held out as test; the rest is training.
- **Metrics** (computed at K, default K=10):
  - Precision@K, Recall@K, NDCG@K — ranking quality
  - Coverage — fraction of catalog items appearing in any user's recs
  - Diversity — `1 − mean pairwise Jaccard` across user reclists
  - Novelty — `mean(−log2 p(item))` where p is item-popularity in train
- **Sampling**: by default 300–500 random eval users (`--max-eval-users`).

## Two-tower notes

- User tower: mean-pooled item-history embedding ⊕ user embedding → MLP → L2-norm.
- Item tower: item embedding (⊕ genre EmbeddingBag for movies) → MLP → L2-norm.
- Loss: symmetric in-batch sampled softmax with temperature 0.07.
- After training, all item vectors are cached; serving is a single `u · V^T`.

## Datasets

| Dataset | Source | Size | License |
|---|---|---|---|
| MovieLens-100K | <https://files.grouplens.org/datasets/movielens/ml-100k.zip> | 5 MB | GroupLens research use |
| MIND-small | HuggingFace mirror `Recommenders/MIND` | 83 MB | Microsoft research use |

The original Azure URLs for MIND were deprecated in July 2024; the loader uses the HuggingFace mirror.

## Reproducibility

All splits and the two-tower model use `seed=42`. ALS and item-kNN are deterministic given the seeded sparse matrix.

## What "research / experimentation" means here

This is a comparison harness, not a production recommender. Things deliberately *not* included: online learning, A/B test framework, cold-start strategies beyond popularity, session-based recurrence, embedding-store integration. Everything fits in memory, trains in minutes on a laptop CPU.
