---
name: benchmark
description: Run model benchmarks through the local benchmark service. Use when the user asks to test a model, run GSM8K, MMLU, HLE, GAIA, or another dataset, or to read experiment scores.
---

# 模型评测

评测服务跑在使用者自己的机器上，默认地址是 `http://127.0.0.1:8000`。用环境变量 `BENCHMARK_API_BASE` 可以改地址。模型 API Key 只交给评测服务，不要写进对话摘要、提交或插件配置。

按这个顺序操作：

1. 调用 `benchmark_health`。服务没启动时，告诉用户先启动评测台，不要假装已经开跑。
2. 用 `benchmark_list_models` 和 `benchmark_list_datasets` 确认模型配置 ID 和数据集 ID。
3. 用户给出新的模型地址和 Key 时，先 `benchmark_test_model`，成功后再 `benchmark_register_model`。
4. `benchmark_create_experiment` 创建实验。HLE 必须带 `hle_judge_model_config_id`。私有研究题只有用户明确要求检索时才打开 `investment_retrieval`。
5. `benchmark_start_experiment` 开始跑题。跑题会调用模型并产生费用，先向用户确认。
6. 用 `benchmark_get_experiment` 汇报状态、交付数、正确数，以及少量失败题编号。不要复述题面和标准答案。
