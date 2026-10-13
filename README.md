# 模型评测 Agent 插件

让 Claude Code、Cursor、DeepSeek Harness，以及任何支持 MCP 的 Agent，操作使用者自己的模型评测服务。

插件不包含评测台源码、题库、实验数据库或模型 API Key。评测服务需要另外在本机运行，默认地址是 `http://127.0.0.1:8000`。可以用环境变量 `BENCHMARK_API_BASE` 修改。

## 公共命令

在仓库根目录执行：

```powershell
python core/cli.py health
python core/cli.py datasets
python core/cli.py models
python core/cli.py experiments
python core/cli.py experiment 1
python core/cli.py create-experiment --name 试跑 --model-id 1 --dataset-id 2 --limit 5
python core/cli.py start-experiment 1
```

登记或测试模型时通过参数传入 Key。命令输出会把 Key 遮住。

## MCP

Copilot、Devin、Claude Desktop 以及其他 MCP 客户端使用 `mcp/server.py`。示例配置在 `mcp/mcp-config.example.json`。把其中的 `args` 改成这台机器上 `mcp/server.py` 的绝对路径。

提供的工具：

- `benchmark_health`
- `benchmark_list_models`
- `benchmark_list_datasets`
- `benchmark_list_experiments`
- `benchmark_get_experiment`
- `benchmark_register_model`
- `benchmark_test_model`
- `benchmark_create_experiment`
- `benchmark_start_experiment`

## Claude Code

在仓库根目录执行：

```text
/plugin marketplace add ./claude-code
/plugin install benchmark-agent@benchmark-agent
```

## Cursor

```powershell
powershell -File cursor/install.ps1
```

重新打开 Cursor，在设置的插件列表中确认「模型评测」。若要让 Agent 直接调用工具，再按 MCP 示例注册 `mcp/server.py`。

## DeepSeek Harness

在 DeepSeek Harness 的 profile 中加入本目录的 `dsh` 包，或在源码目录执行：

```powershell
dsh web --patch ./dsh/cordis.patch.yml
```

插件会调用仓库根目录的 `core/cli.py`。

## 使用约定

启动实验会真实调用模型并产生费用。Agent 应先向用户确认模型、数据集和题量。HLE 必须另选 Judge 模型。回复里只报告状态和分数，不复述题面、标准答案或 API Key。
