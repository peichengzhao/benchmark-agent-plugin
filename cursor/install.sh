#!/usr/bin/env bash
set -euo pipefail
source_dir="$(cd "$(dirname "$0")" && pwd)"
dest="${HOME}/.cursor/plugins/local/benchmark-agent"
mkdir -p "$dest"
cp -R "$source_dir"/. "$dest"/
echo "已安装到 $dest"
echo "重新打开 Cursor 后，在设置的插件列表中确认“模型评测”。"
