---
name: benchmark
description: Run model benchmarks through the local benchmark service. Use when the user asks to test a model, run GSM8K, MMLU, HLE, GAIA, or another dataset, or to read experiment scores.
---

# 模型评测

评测服务跑在使用者自己的机器上，默认地址是 `http://127.0.0.1:8000`。用环境变量 `BENCHMARK_API_BASE` 可以改地址。模型 API Key 只交给评测服务，不要写进对话摘要、提交或插件配置。

有 MCP 工具时调用这些工具。没有 MCP 时，在本仓库根目录运行 `python core/cli.py <命令>`，把 JSON 结果读回来。

按这个顺序操作：

1. `health`。服务没启动时，告诉用户先启动评测台。
2. `models` 和 `datasets`，确认模型配置 ID 和数据集 ID。
3. 新模型先 `test-model`，成功后再 `register-model`。
4. `create-experiment`。HLE 必须带 `--judge-id`。
5. 用户确认后，再 `start-experiment`。跑题会调用模型并产生费用。
6. `experiment <id>` 只汇报状态、分数和少量失败题编号，不复述题面和标准答案。
