<div align="center">
  <h1>⚡ RecSys Lab</h1>
  <p><strong>Production-Grade Recommendation Systems Research Harness</strong></p>
  <p>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python"></a>
    <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.110+-green" alt="FastAPI"></a>
    <a href="https://nextjs.org/"><img src="https://img.shields.io/badge/Next.js-16-black" alt="Next.js"></a>
    <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Docker-Ready-2496ED" alt="Docker"></a>
    <a href="https://mlflow.org/"><img src="https://img.shields.io/badge/MLflow-Integrated-orange" alt="MLflow"></a>
    <a href="https://qdrant.tech/"><img src="https://img.shields.io/badge/Qdrant-Vector--DB-red" alt="Qdrant"></a>
    <a href="https://kubernetes.io/"><img src="https://img.shields.io/badge/K8s-Ready-326CE5" alt="Kubernetes"></a>
    <a href="https://www.evidentlyai.com/"><img src="https://img.shields.io/badge/Evidently-Monitoring-FF6B6B" alt="Evidently"></a>
    <a href="https://github.com/Aayush7352/Recommendation-Systems/actions"><img src="https://img.shields.io/github/actions/workflow/status/Aayush7352/Recommendation-Systems/ci.yml?branch=main" alt="CI"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
  </p>
  <p>
    <strong>6 algorithms · 2 domains (Movies + News) · Side-by-side comparison · Vector search · MLOps · Docker · K8s</strong>
  </p>
</div>

---

## 🚀 Overview

RecSys Lab is a **production-ready, end-to-end recommendation systems platform** that trains 6 different algorithms across 2 real-world datasets and exposes them via a unified API + UI for side-by-side comparison, evaluation, and analysis.

Unlike typical recsys projects that are either Jupyter notebooks or toy demos, this is a **full-stack, MLOps-enabled platform** ready for research, experimentation, and production deployment.

### ✨ What Makes This Unique

| Feature | Description |
|---|---|
| **6 Algorithms, 1 Harness** | Baseline → Content → Collaborative → Hybrid → Neural — all comparable |
| **2 Real Domains** | MovieLens-100K + Microsoft MIND-small with domain-specific features |
| **Vector ANN Search** | Qdrant-powered Approximate Nearest Neighbor for sub-millisecond serving |
| **Cold-Start Search** | Semantic text search via TF-IDF content embeddings in Qdrant |
| **MLflow Tracking** | Every train/evaluate run logged with params, metrics, and artifacts |
| **Docker Compose** | One command: backend + frontend + Qdrant + MLflow |
| **Kubernetes Ready** | Full manifests for production deployment |
| **Drift Monitoring** | PSI/JS-divergence based data & model drift detection |
| **A/B Testing** | Built-in framework for online model comparison |
| **CI/CD Pipeline** | GitHub Actions: lint, test, train, evaluate, deploy |
| **Production Logging** | Structured logging (structlog) across all services |
| **Beautiful UI** | Next.js + Tailwind with side-by-side comparison views |

---

## 🧠 Algorithms

| Algorithm | Family | Key Technique |
|---|---|---|
| `popularity` | 📊 Baseline | Global most-popular count |
| `content_based` | 📝 Content | TF-IDF + user profile aggregation |
| `item_knn` | 🤝 Collaborative (memory) | Item-item cosine similarity k-NN |
| `als` | 🧮 Collaborative (model) | Implicit ALS matrix factorization |
| `hybrid` | 🔀 Hybrid | Weighted blend: content + ALS |
| `two_tower` | 🧠 Neural | PyTorch dual-tower with in-batch sampled softmax |

All models implement the same `BaseRecommender` interface (`fit`, `recommend`, `recommend_batch`) — making it trivial to add new algorithms.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                            Frontend                                 │
│                    Next.js 16 + Tailwind CSS                        │
│                    http://localhost:3000                             │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ REST API
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                            Backend                                  │
│                    FastAPI + uvicorn                                 │
│                    http://localhost:8000                             │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │ Recommenders │  │ Evaluation  │  │  Monitoring │  │ Cold Start│ │
│  │  6 Models    │  │  Precision  │  │  Drift Det. │  │  Search   │ │
│  └──────┬──────┘  │  Recall etc  │  └─────────────┘  └─────┬─────┘ │
│         │         └─────────────┘                          │       │
│         ▼                                                   │       │
│  ┌──────────────────────────────────────────────────┐       │       │
│  │           Qdrant Vector Database                  │◄──────┘       │
│  │     ANN Search · Cold-Start Index                 │               │
│  └──────────────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌────────────────┐
│   MLflow     │  │   Qdrant     │  │   PostgreSQL   │
│ Experimental │  │  Vector DB   │  │  (optional)    │
│   Tracking   │  │  port 6333   │  │                │
└──────────────┘  └──────────────┘  └────────────────┘
```

---

## 🛠️ Quick Start

### Option A: Docker Compose (Recommended)

```bash
docker compose up -d
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| MLflow UI | http://localhost:5000 |
| Qdrant Dashboard | http://localhost:6333/dashboard |

### Option B: Local Development

**1. Backend**
```bash
python3 -m venv .venv
.venv/bin/pip install -e ./backend[dev]
.venv/bin/python -m recsys.cli train        # Train all models
.venv/bin/python -m recsys.cli evaluate --k 10  # Evaluate
.venv/bin/uvicorn recsys.api.main:app --reload --port 8000
```

**2. Frontend**
```bash
cd frontend
npm install
npm run dev
```

---

## 📡 API Reference

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Service info + trained domains |
| `GET` | `/domains/{domain}/info` | User/item/interaction stats |
| `GET` | `/domains/{domain}/users` | Top users by interactions |
| `GET` | `/domains/{domain}/users/{id}/history` | User interaction history |
| `GET` | `/domains/{domain}/items` | Sample items catalog |
| `GET` | `/recommend/{domain}/{algo}/{user_id}` | Top-K recommendations |
| `GET` | `/recommend/{domain}/compare/{user_id}` | Side-by-side across algos |
| `GET` | `/search/{domain}?q=keyword` | Semantic cold-start search |
| `GET` | `/evaluate/{domain}` | Offline evaluation report |
| `GET` | `/ab-test/{domain}/{user_id}` | A/B test two models |
| `GET` | `/monitor/drift/{domain}` | Data drift report |
| `GET` | `/monitor/drift/{domain}/{model}` | Model drift report |

---

## 📊 Evaluation Protocol

- **Split**: Leave-one-out per user (last interaction by timestamp = test)
- **Metrics** (at K=10):
  - `Precision@K` · `Recall@K` · `NDCG@K` — Ranking quality
  - `Coverage` — % of catalog in any user's recs
  - `Diversity` — 1 − mean pairwise Jaccard across users
  - `Novelty` — mean(−log₂ p(item)) where p = item popularity

---

## 🧪 MLOps Features

### MLflow Experiment Tracking
```bash
.venv/bin/python -m recsys.cli train --mlflow
.venv/bin/python -m recsys.cli evaluate --k 10 --mlflow
```
Then open http://localhost:5000 to view runs.

### Drift Monitoring
```bash
curl http://localhost:8000/monitor/drift/movies
curl http://localhost:8000/monitor/drift/movies/als
```

### A/B Testing
```bash
curl "http://localhost:8000/ab-test/movies/1?model_a=popularity&model_b=two_tower"
```

---

## 🐳 Docker Compose Services

```yaml
services:
  backend:   # FastAPI + recommenders + monitoring
  frontend:  # Next.js UI
  qdrant:    # Vector database for ANN + cold-start
  mlflow:    # Experiment tracking
```

---

## ☸️ Kubernetes Deployment

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/
```

Includes: Deployments, Services, StatefulSet (Qdrant), Ingress, PVCs.

---

## 🧩 Project Structure

```
├── backend/
│   ├── recsys/
│   │   ├── api/              FastAPI routes
│   │   ├── data/             Dataset loaders (MovieLens, MIND)
│   │   ├── models/           6 recommender implementations
│   │   │   ├── base.py       Abstract recommender interface
│   │   │   ├── popularity.py
│   │   │   ├── content_based.py
│   │   │   ├── collaborative.py  (ALS + ItemKNN)
│   │   │   ├── hybrid.py
│   │   │   ├── two_tower.py      PyTorch neural
│   │   │   └── cold_start.py     Semantic search
│   │   ├── evaluation/       Metrics & offline evaluation
│   │   ├── cli.py            Training/evaluation CLI
│   │   ├── registry.py       Model persistence
│   │   ├── tracking.py       MLflow integration
│   │   ├── vector_store.py   Qdrant client wrapper
│   │   ├── monitoring.py     Drift detection
│   │   └── ab_testing.py     A/B test framework
│   └── tests/                Pytest suite
├── frontend/                 Next.js 16 + Tailwind CSS
├── k8s/                      Kubernetes manifests
├── data/                     Raw/artifacts/monitoring
├── docker-compose.yml
└── .github/workflows/        CI/CD pipelines
```

---

## 📈 Roadmap

- [x] 6 recommendation algorithms + 2 domains
- [x] FastAPI backend + Next.js UI
- [x] Docker Compose + K8s manifests
- [x] Qdrant vector DB for ANN search
- [x] Cold-start semantic search
- [x] MLflow experiment tracking
- [x] Drift monitoring (Evidently-style)
- [x] A/B testing framework
- [x] CI/CD pipelines
- [ ] Session-based models (GRU4Rec, SR-GNN)
- [ ] LLM-enhanced embeddings
- [ ] Real-time online learning
- [ ] Feature store (Feast)

---

## 🤝 Contributing

Contributions welcome! Check [issues](https://github.com/Aayush7352/Recommendation-Systems/issues) for open tasks.

```bash
git clone https://github.com/Aayush7352/Recommendation-Systems.git
cd Recommendation-Systems
.venv/bin/pip install -e "./backend[dev]"
.venv/bin/pytest backend/tests -v
```

---

## 📜 License

MIT © [Aayush](https://github.com/Aayush7352)

---

<div align="center">
  <sub>Built with ❤️ for the recommendation systems community</sub>
</div>
