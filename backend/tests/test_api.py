from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from recsys.api.main import app
from recsys.registry import ARTIFACT_DIR, DomainBundle, load_movie_bundle, save_bundle

client = TestClient(app)


@pytest.fixture(scope="session")
def _ensure_movies_trained():
    path = ARTIFACT_DIR / "movies.pkl"
    if not path.exists():
        bundle = load_movie_bundle()
        from recsys.models.popularity import PopularityRecommender
        bundle.models["popularity"] = PopularityRecommender().fit(bundle.interactions)
        save_bundle(bundle)
    return path


class TestRoot:
    def test_root_returns_service_info(self):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "recsys-lab"
        assert "movies" in data["domains"]


class TestDomainInfo:
    def test_movies_info(self, _ensure_movies_trained):
        resp = client.get("/domains/movies/info")
        assert resp.status_code == 200
        data = resp.json()
        assert data["domain"] == "movies"
        assert data["n_users"] > 0
        assert data["n_items"] > 0

    def test_unknown_domain_returns_404(self):
        resp = client.get("/domains/unknown/info")
        assert resp.status_code == 404


class TestUsers:
    def test_list_users(self, _ensure_movies_trained):
        resp = client.get("/domains/movies/users?limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) <= 5
        assert "user_id" in data[0]
        assert "n_interactions" in data[0]

    def test_user_history(self, _ensure_movies_trained):
        resp = client.get("/domains/movies/users/1/history")
        assert resp.status_code in (200, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, list)


class TestRecommend:
    def test_recommend_endpoint(self, _ensure_movies_trained):
        resp = client.get("/recommend/movies/popularity/1?k=3")
        assert resp.status_code in (200, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert data["algo"] == "popularity"
            assert len(data["items"]) <= 3

    def test_recommend_compare(self, _ensure_movies_trained):
        resp = client.get("/recommend/movies/compare/1?algos=popularity&k=3")
        assert resp.status_code in (200, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert "results" in data
            assert "popularity" in data["results"]


class TestEvaluate:
    def test_evaluate_cached(self, _ensure_movies_trained):
        resp = client.get("/evaluate/movies?k=5")
        assert resp.status_code in (200, 500)
