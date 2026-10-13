"""Command line for host plugins that shell out to the shared client."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.client import BenchmarkError  # noqa: E402
from core import client  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Call a local benchmark service")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("health")
    sub.add_parser("models")
    sub.add_parser("datasets")
    sub.add_parser("experiments")

    experiment = sub.add_parser("experiment")
    experiment.add_argument("id", type=int)

    register = sub.add_parser("register-model")
    _model_flags(register)

    test = sub.add_parser("test-model")
    _model_flags(test)

    create = sub.add_parser("create-experiment")
    create.add_argument("--name", required=True)
    create.add_argument("--model-id", required=True, type=int)
    create.add_argument("--dataset-id", required=True, type=int)
    create.add_argument("--limit", type=int)
    create.add_argument("--judge-id", type=int)
    create.add_argument("--investment-retrieval", action="store_true")

    start = sub.add_parser("start-experiment")
    start.add_argument("id", type=int)

    args = parser.parse_args(argv)
    try:
        result = _dispatch(args)
    except BenchmarkError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


def _model_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--name", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--endpoint", default="chat/completions")


def _dispatch(args):
    if args.command == "health":
        return client.health()
    if args.command == "models":
        return client.list_models()
    if args.command == "datasets":
        return client.list_datasets()
    if args.command == "experiments":
        return client.list_experiments()
    if args.command == "experiment":
        return client.get_experiment(args.id)
    if args.command == "register-model":
        return client.register_model(args.name, args.base_url, args.model, args.api_key, args.endpoint)
    if args.command == "test-model":
        return client.test_model(args.name, args.base_url, args.model, args.api_key, args.endpoint)
    if args.command == "create-experiment":
        return client.create_experiment(args.name, args.model_id, args.dataset_id, args.limit, args.judge_id, args.investment_retrieval)
    if args.command == "start-experiment":
        return client.start_experiment(args.id)
    raise BenchmarkError(f"未知命令 {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
