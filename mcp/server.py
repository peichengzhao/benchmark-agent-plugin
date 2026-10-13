#!/usr/bin/env python3
"""MCP server for the local benchmark service. Standard library only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.client import BenchmarkError  # noqa: E402
from core import client  # noqa: E402

PROTOCOL_VERSION = "2024-11-05"

TOOLS = [
    {
        "name": "benchmark_health",
        "description": "Check that the local benchmark service is running.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "benchmark_list_models",
        "description": "List model configurations. API keys are masked.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "benchmark_list_datasets",
        "description": "List imported datasets with id, name, adapter, and item count.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "benchmark_list_experiments",
        "description": "List experiments with status and score summary.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "benchmark_get_experiment",
        "description": "Get one experiment summary and a short sample of failed or incorrect items. Does not return prompts or secrets.",
        "inputSchema": {
            "type": "object",
            "properties": {"experiment_id": {"type": "integer"}},
            "required": ["experiment_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "benchmark_register_model",
        "description": "Save an OpenAI-compatible model on the local benchmark service. The key stays in that service.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "base_url": {"type": "string"},
                "model": {"type": "string"},
                "api_key": {"type": "string"},
                "endpoint": {"type": "string"},
            },
            "required": ["name", "base_url", "model", "api_key"],
            "additionalProperties": False,
        },
    },
    {
        "name": "benchmark_test_model",
        "description": "Ask the benchmark service to test a model connection. The service waits about 30 seconds.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "base_url": {"type": "string"},
                "model": {"type": "string"},
                "api_key": {"type": "string"},
                "endpoint": {"type": "string"},
            },
            "required": ["name", "base_url", "model", "api_key"],
            "additionalProperties": False,
        },
    },
    {
        "name": "benchmark_create_experiment",
        "description": "Create an experiment for one saved model and one dataset. HLE also needs hle_judge_model_config_id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "model_config_id": {"type": "integer"},
                "dataset_id": {"type": "integer"},
                "limit": {"type": "integer"},
                "hle_judge_model_config_id": {"type": "integer"},
                "investment_retrieval": {"type": "boolean"},
            },
            "required": ["name", "model_config_id", "dataset_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "benchmark_start_experiment",
        "description": "Start an existing experiment. Questions run on the local benchmark service.",
        "inputSchema": {
            "type": "object",
            "properties": {"experiment_id": {"type": "integer"}},
            "required": ["experiment_id"],
            "additionalProperties": False,
        },
    },
]
_BY_NAME = {tool["name"]: tool for tool in TOOLS}


def _call(name: str, arguments: dict):
    if name == "benchmark_health":
        return client.health()
    if name == "benchmark_list_models":
        return client.list_models()
    if name == "benchmark_list_datasets":
        return client.list_datasets()
    if name == "benchmark_list_experiments":
        return client.list_experiments()
    if name == "benchmark_get_experiment":
        return client.get_experiment(arguments["experiment_id"])
    if name == "benchmark_register_model":
        return client.register_model(arguments["name"], arguments["base_url"], arguments["model"], arguments["api_key"], arguments.get("endpoint", "chat/completions"))
    if name == "benchmark_test_model":
        return client.test_model(arguments["name"], arguments["base_url"], arguments["model"], arguments["api_key"], arguments.get("endpoint", "chat/completions"))
    if name == "benchmark_create_experiment":
        return client.create_experiment(
            arguments["name"],
            arguments["model_config_id"],
            arguments["dataset_id"],
            arguments.get("limit"),
            arguments.get("hle_judge_model_config_id"),
            arguments.get("investment_retrieval", False),
        )
    if name == "benchmark_start_experiment":
        return client.start_experiment(arguments["experiment_id"])
    raise BenchmarkError(f"未知工具 {name}")


def _result(id_, result):
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _error(id_, code, message):
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def handle(req: object):
    if not isinstance(req, dict) or req.get("jsonrpc") != "2.0":
        return _error(None, -32600, "invalid request")
    method = req.get("method")
    id_ = req.get("id")
    params = req.get("params") or {}
    if method == "initialize":
        return _result(id_, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "benchmark-agent", "version": "0.1.0"},
        })
    if method in {"notifications/initialized", "initialized"}:
        return None
    if method == "ping":
        return _result(id_, {})
    if method == "tools/list":
        return _result(id_, {"tools": TOOLS})
    if method == "tools/call":
        name = params.get("name")
        tool = _BY_NAME.get(name)
        if not tool:
            return _error(id_, -32602, f"unknown tool: {name}")
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            return _error(id_, -32602, "arguments must be an object")
        try:
            payload = _call(name, arguments)
        except (BenchmarkError, KeyError, TypeError, ValueError) as exc:
            text = str(exc).replace(arguments.get("api_key", "___none___"), "••••••••")
            return _result(id_, {"content": [{"type": "text", "text": text}], "isError": True})
        text = json.dumps(payload, ensure_ascii=False)
        if arguments.get("api_key"):
            text = text.replace(arguments["api_key"], "••••••••")
        return _result(id_, {"content": [{"type": "text", "text": text}], "isError": False})
    return _error(id_, -32601, f"method not found: {method}")


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            resp = _error(None, -32700, "parse error")
        else:
            resp = handle(req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
