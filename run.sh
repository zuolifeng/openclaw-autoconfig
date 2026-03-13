#!/usr/bin/env bash
# OpenClaw 自动配置工具 - 启动脚本
# 用法：bash run.sh [--cli]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 检查 Python3
if ! command -v python3 &>/dev/null; then
    echo "[错误] 未检测到 Python3，请先安装 Python 3.8+"
    exit 1
fi

# 检查 tkinter 是否可用
if python3 -c "import tkinter" 2>/dev/null; then
    echo "[INFO] 启动 GUI 界面..."
    python3 "$SCRIPT_DIR/main.py"
else
    echo "[WARN] 当前环境不支持 GUI（tkinter 不可用），切换为命令行模式"
    bash "$SCRIPT_DIR/scripts/install.sh"
fi
