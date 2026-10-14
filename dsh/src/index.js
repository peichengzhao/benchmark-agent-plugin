import { spawn } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import Schema from "@deepseek-ai/schemastery";
import { defineTool } from "@deepseek-ai/dsh-tools";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");

export const name = "benchmark";
export const inject = ["tools"];

export const Config = Schema.object({
  pythonCmd: Schema.string().default("python").description("Python used to run core/cli.py"),
  apiBase: Schema.string().default("http://127.0.0.1:8000").description("Local benchmark service"),
});

function run(config, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(config.pythonCmd || "python", [join(ROOT, "core", "cli.py"), ...args], {
      cwd: ROOT,
      env: { ...process.env, BENCHMARK_API_BASE: config.apiBase || "http://127.0.0.1:8000" },
    });
    let out = "";
    let err = "";
    child.stdout.on("data", (chunk) => { out += chunk; });
    child.stderr.on("data", (chunk) => { err += chunk; });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) resolve(out.trim());
      else reject(new Error(out.trim() || err.trim() || `exit ${code}`));
    });
  });
}

// Every tool hands the CLI's stdout back as plain text. An explicit `output`
// declaration is required since dsh-tools 0.2.0-rc.2.
const TEXT_OUTPUT = {
  schema: { type: "string" },
  render: (_args, value) => [{ type: "text", text: String(value ?? "") }],
};

const tools = [
  ["benchmark_health", "检查本机评测服务是否在运行。", {}, ["health"]],
  ["benchmark_list_models", "列出已保存的模型配置，不返回 API Key。", {}, ["models"]],
  ["benchmark_list_datasets", "列出已导入的数据集。", {}, ["datasets"]],
  ["benchmark_list_experiments", "列出实验和分数摘要。", {}, ["experiments"]],
];

export function apply(ctx, config) {
  for (const [name, description, parameters, args] of tools) {
    ctx.tools.register(defineTool({
      name,
      description,
      parameters,
      output: TEXT_OUTPUT,
      async execute() {
        return run(config, args);
      },
    }));
  }
  ctx.tools.register(defineTool({
    name: "benchmark_get_experiment",
    description: "查看一个实验的状态、分数和少量失败题编号。",
    parameters: { experimentId: { type: "number", description: "实验 ID" } },
    output: TEXT_OUTPUT,
    async execute(args) {
      return run(config, ["experiment", String(args.experimentId)]);
    },
  }));
  ctx.tools.register(defineTool({
    name: "benchmark_create_experiment",
    description: "用已保存的模型和数据集创建实验。HLE 需要 judgeId。",
    parameters: {
      name: { type: "string", description: "实验名称" },
      modelId: { type: "number", description: "模型配置 ID" },
      datasetId: { type: "number", description: "数据集 ID" },
      limit: { type: "number", description: "只跑前 N 题，可省略" },
      judgeId: { type: "number", description: "HLE Judge 配置 ID" },
    },
    output: TEXT_OUTPUT,
    async execute(args) {
      const argv = ["create-experiment", "--name", args.name, "--model-id", String(args.modelId), "--dataset-id", String(args.datasetId)];
      if (args.limit) argv.push("--limit", String(args.limit));
      if (args.judgeId) argv.push("--judge-id", String(args.judgeId));
      return run(config, argv);
    },
  }));
  ctx.tools.register(defineTool({
    name: "benchmark_start_experiment",
    description: "开始运行实验。会调用模型并产生费用，先向用户确认。",
    parameters: { experimentId: { type: "number", description: "实验 ID" } },
    output: TEXT_OUTPUT,
    async execute(args) {
      return run(config, ["start-experiment", String(args.experimentId)]);
    },
  }));
}
