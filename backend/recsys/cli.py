from __future__ import annotations

import argparse
import json
import os
import sys
import time

import structlog

from .evaluation.runner import evaluate_models
from .registry import (
    DOMAINS,
    load_movie_bundle,
    load_news_bundle,
    save_bundle,
    train_domain,
)
from .tracking import ExperimentTracker

logger = structlog.get_logger()


def cmd_train(args: argparse.Namespace) -> int:
    domains = args.domains or list(DOMAINS)
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    tracker = ExperimentTracker("recsys", tracking_uri=tracking_uri) if args.mlflow else None
    for d in domains:
        logger.info("training_domain", domain=d)
        t0 = time.time()
        if d == "movies":
            bundle = load_movie_bundle()
        elif d == "news":
            bundle = load_news_bundle(max_users=args.max_news_users)
        else:
            logger.error("unknown_domain", domain=d)
            return 2
        bundle = train_domain(bundle, tracker=tracker)
        path = save_bundle(bundle)
        elapsed = round(time.time() - t0, 1)
        logger.info("domain_trained", domain=d, path=str(path), elapsed_seconds=elapsed, models=list(bundle.models.keys()))
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    domains = args.domains or list(DOMAINS)
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    tracker = ExperimentTracker("recsys", tracking_uri=tracking_uri) if args.mlflow else None
    results: dict = {}
    for d in domains:
        logger.info("evaluating_domain", domain=d)
        if d == "movies":
            bundle = load_movie_bundle()
        elif d == "news":
            bundle = load_news_bundle(max_users=args.max_news_users)
        else:
            logger.error("unknown_domain", domain=d)
            return 2
        from .registry import _build_movie_models, _build_news_models
        builder = _build_movie_models if d == "movies" else _build_news_models
        models = builder()
        result = evaluate_models(
            domain=d,
            models=models,
            interactions=bundle.interactions,
            items=bundle.items,
            users=bundle.users,
            k=args.k,
            max_eval_users=args.max_eval_users,
        )
        results[d] = result.as_dict()
        for r in result.reports:
            logger.info("eval_result", algo=r.algo, k=r.k, precision=r.precision, recall=r.recall, ndcg=r.ndcg, coverage=r.coverage)
        if tracker:
            tracker.log_evaluation(d, args.k, {}, {r.algo: {"precision": r.precision, "recall": r.recall, "ndcg": r.ndcg} for r in result.reports})
    if args.out:
        with open(args.out, "w") as f:
            json.dump(results, f, indent=2)
        logger.info("eval_written", path=args.out)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="recsys")
    sub = p.add_subparsers(dest="cmd", required=True)

    pt = sub.add_parser("train", help="Train and persist all models per domain")
    pt.add_argument("--domains", nargs="*", choices=DOMAINS)
    pt.add_argument("--max-news-users", type=int, default=5000)
    pt.add_argument("--mlflow", action="store_true", help="Log training to MLflow")
    pt.set_defaults(func=cmd_train)

    pe = sub.add_parser("evaluate", help="Run offline evaluation across all algos")
    pe.add_argument("--domains", nargs="*", choices=DOMAINS)
    pe.add_argument("--k", type=int, default=10)
    pe.add_argument("--max-eval-users", type=int, default=500)
    pe.add_argument("--max-news-users", type=int, default=5000)
    pe.add_argument("--out", type=str, default=None)
    pe.add_argument("--mlflow", action="store_true", help="Log evaluation to MLflow")
    pe.set_defaults(func=cmd_evaluate)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
