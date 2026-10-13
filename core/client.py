"""HTTP client for a locally running benchmark service.

The service keeps model credentials. This client never prints them, and it
strips secret-shaped fields from any payload it returns to an agent.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

DEFAULT_BASE = "http://127.0.0.1:8000"
_SECRET_KEYS = {"api_key", "search_api_key", "authorization", "token"}


class BenchmarkError(RuntimeError):
    pass


def base_url() -> str:
    return os.environ.get("BENCHMARK_API_BASE", DEFAULT_BASE).rstrip("/")


def _redact(value):
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            if key.lower() in _SECRET_KEYS:
                cleaned[key] = "••••••••" if item else ""
            else:
                cleaned[key] = _redact(item)
        return cleaned
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def request(method: str, path: str, body: dict | None = None, timeout: float = 60):
    url = f"{base_url()}{path}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(detail)
            detail = parsed.get("detail", detail)
        except json.JSONDecodeError:
            pass
        raise BenchmarkError(f"{exc.code} {detail}") from exc
    except urllib.error.URLError as exc:
        raise BenchmarkError(
            f"无法连接评测服务 {base_url()}。请先在本机启动评测台。原因：{exc.reason}"
        ) from exc
    return _redact(payload)


def health():
    return request("GET", "/api/health", timeout=10)


def list_models():
    return request("GET", "/api/models")


def list_datasets():
    rows = request("GET", "/api/datasets")
    return [
        {
            "id": row.get("id"),
            "name": row.get("name"),
            "adapter_id": row.get("adapter_id"),
            "version": row.get("version"),
            "item_count": row.get("item_count"),
        }
        for row in rows
    ]


def list_experiments():
    rows = request("GET", "/api/experiments")
    return [_experiment_summary(row) for row in rows]


def get_experiment(experiment_id: int):
    detail = request("GET", f"/api/experiments/{int(experiment_id)}", timeout=120)
    summary = _experiment_summary(detail)
    runs = detail.get("runs") or []
    problems = []
    for run in runs:
        if run.get("status") in {"failed", "incomplete"} or run.get("passed") is False:
            problems.append({
                "id": run.get("id"),
                "external_id": run.get("external_id"),
                "status": run.get("status"),
                "passed": run.get("passed"),
                "score": run.get("score"),
            })
            if len(problems) >= 8:
                break
    summary["problem_sample"] = problems
    summary["delivery_metrics"] = detail.get("delivery_metrics")
    return summary


def register_model(name: str, base_url_value: str, model: str, api_key: str, endpoint: str = "chat/completions"):
    return request("POST", "/api/models", {
        "name": name,
        "base_url": base_url_value,
        "model": model,
        "api_key": api_key,
        "endpoint": endpoint,
    })


def test_model(name: str, base_url_value: str, model: str, api_key: str, endpoint: str = "chat/completions"):
    return request("POST", "/api/models/test", {
        "name": name,
        "base_url": base_url_value,
        "model": model,
        "api_key": api_key,
        "endpoint": endpoint,
    }, timeout=45)


def create_experiment(name: str, model_config_id: int, dataset_id: int, limit: int | None = None, hle_judge_model_config_id: int | None = None, investment_retrieval: bool = False):
    body = {
        "name": name,
        "model_config_id": int(model_config_id),
        "dataset_id": int(dataset_id),
        "temperature": 0,
        "timeout": 0,
        "concurrency": 2,
        "investment_retrieval": bool(investment_retrieval),
    }
    if limit is not None:
        body["limit"] = int(limit)
    if hle_judge_model_config_id is not None:
        body["hle_judge_model_config_id"] = int(hle_judge_model_config_id)
    created = request("POST", "/api/experiments", body)
    return {"id": created.get("id"), "name": created.get("name"), "status": created.get("status"), "total": created.get("total")}


def start_experiment(experiment_id: int):
    return request("POST", f"/api/experiments/{int(experiment_id)}/start")


def _experiment_summary(row: dict) -> dict:
    answered = row.get("answered")
    passed = None
    metrics = row.get("delivery_metrics") or {}
    if metrics:
        answered = metrics.get("answered", answered)
        passed = metrics.get("passed")
    return {
        "id": row.get("id"),
        "name": row.get("name"),
        "status": row.get("status"),
        "model_name": row.get("model_name"),
        "model": row.get("model"),
        "dataset_name": row.get("dataset_name"),
        "dataset_adapter": row.get("dataset_adapter"),
        "total": row.get("total"),
        "answered": answered,
        "passed": passed,
        "average_score": row.get("average_score"),
    }
