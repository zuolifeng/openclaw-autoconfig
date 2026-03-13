#!/usr/bin/env bash
# 进程状态检测脚本 - 输出 JSON 格式供 GUI 读取

check_process() {
    local name="$1"
    if pgrep -x "$name" &>/dev/null; then
        echo "running"
    else
        echo "stopped"
    fi
}

get_openclaw_info() {
    local status
    status=$(check_process "openclaw")

    local version="unknown"
    if command -v openclaw &>/dev/null; then
        version=$(openclaw --version 2>/dev/null || echo "unknown")
    fi

    local pid=""
    if [ "$status" = "running" ]; then
        pid=$(pgrep -x "openclaw" | head -1)
    fi

    local config_file=""
    if [ -f "$HOME/.openclaw/config.json" ]; then
        config_file="$HOME/.openclaw/config.json"
    fi

    printf '{"status":"%s","version":"%s","pid":"%s","config":"%s","installed":%s}\n' \
        "$status" \
        "$version" \
        "$pid" \
        "$config_file" \
        "$(command -v openclaw &>/dev/null && echo 'true' || echo 'false')"
}

get_openclaw_info
