---
name: benchmark
description: Run model benchmarks through the local benchmark service. Use when the user asks to test a model, run a dataset, or read experiment scores.
---

# 模型评测

使用 `benchmark_health`、`benchmark_list_models`、`benchmark_list_datasets`、`benchmark_list_experiments`、`benchmark_get_experiment`、`benchmark_create_experiment` 和 `benchmark_start_experiment`。

评测服务在使用者本机，默认 `http://127.0.0.1:8000`。不要把模型 API Key 写进回复。启动实验前先向用户确认。HLE 必须提供 Judge 配置 ID。
