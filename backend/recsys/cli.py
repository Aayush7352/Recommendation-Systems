from __future__ import annotations

import argparse
import json
import sys
import time

from .evaluation.runner import evaluate_models
from .registry import (
    DOMAINS,
    load_movie_bundle,
    load_news_bundle,
    save_bundle,
    train_domain,
)


def cmd_train(args: argparse.Namespace) -> int:
    domains = args.domains or list(DOMAINS)
    for d in domains:
        print(f"\n=== Training domain: {d} ===")
        t0 = time.time()
        if d == "movies":
            bundle = load_movie_bundle()
        elif d == "news":
            bundle = load_news_bundle(max_users=args.max_news_users)
        else:
            print(f"unknown domain: {d}", file=sys.stderr)
            return 2
        bundle = train_domain(bundle)
        path = save_bundle(bundle)
        print(f"  saved -> {path}  ({time.time() - t0:.1f}s)")
        print(f"  models: {list(bundle.models.keys())}")
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    domains = args.domains or list(DOMAINS)
    results: dict = {}
    for d in domains:
        print(f"\n=== Evaluating domain: {d} ===")
        if d == "movies":
            bundle = load_movie_bundle()
        elif d == "news":
            bundle = load_news_bundle(max_users=args.max_news_users)
        else:
            print(f"unknown domain: {d}", file=sys.stderr)
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
            print(f"  {r.algo:15s}  P@{r.k}={r.precision:.4f}  R@{r.k}={r.recall:.4f}  "
                  f"NDCG@{r.k}={r.ndcg:.4f}  cov={r.coverage:.3f}")
    if args.out:
        with open(args.out, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nWrote {args.out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="recsys")
    sub = p.add_subparsers(dest="cmd", required=True)

    pt = sub.add_parser("train", help="Train and persist all models per domain")
    pt.add_argument("--domains", nargs="*", choices=DOMAINS)
    pt.add_argument("--max-news-users", type=int, default=5000)
    pt.set_defaults(func=cmd_train)

    pe = sub.add_parser("evaluate", help="Run offline evaluation across all algos")
    pe.add_argument("--domains", nargs="*", choices=DOMAINS)
    pe.add_argument("--k", type=int, default=10)
    pe.add_argument("--max-eval-users", type=int, default=500)
    pe.add_argument("--max-news-users", type=int, default=5000)
    pe.add_argument("--out", type=str, default=None)
    pe.set_defaults(func=cmd_evaluate)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
