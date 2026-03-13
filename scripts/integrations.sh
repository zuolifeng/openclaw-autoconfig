#!/usr/bin/env bash
# OpenClaw 与聊天软件集成配置脚本
# 支持：飞书、QQ、微信（企业微信）、Telegram、Discord、WhatsApp

set -euo pipefail

BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; }

# 获取 openclaw 配置目录
get_config_dir() {
    if [ -d "$HOME/.openclaw" ]; then
        echo "$HOME/.openclaw"
    else
        mkdir -p "$HOME/.openclaw"
        echo "$HOME/.openclaw"
    fi
}

# 飞书集成配置
setup_feishu() {
    local app_id="$1"
    local app_secret="$2"
    local config_dir
    config_dir=$(get_config_dir)

    info "配置飞书集成..."
    cat > "$config_dir/feishu.json" <<EOF
{
  "platform": "feishu",
  "app_id": "${app_id}",
  "app_secret": "${app_secret}",
  "webhook": "",
  "enabled": true
}
EOF
    # 写入 openclaw 主配置
    update_main_config "feishu" "$config_dir/feishu.json"
    success "飞书集成配置完成"
    echo "INTEGRATION_FEISHU:ok"
}

# QQ 机器人集成
setup_qq() {
    local qq_token="$1"
    local config_dir
    config_dir=$(get_config_dir)

    info "配置 QQ 机器人集成..."
    cat > "$config_dir/qq.json" <<EOF
{
  "platform": "qq",
  "bot_token": "${qq_token}",
  "enabled": true
}
EOF
    update_main_config "qq" "$config_dir/qq.json"
    success "QQ 集成配置完成"
    echo "INTEGRATION_QQ:ok"
}

# 微信/企业微信集成
setup_wechat() {
    local corp_id="$1"
    local corp_secret="$2"
    local config_dir
    config_dir=$(get_config_dir)

    info "配置企业微信集成..."
    cat > "$config_dir/wechat.json" <<EOF
{
  "platform": "wechat_work",
  "corp_id": "${corp_id}",
  "corp_secret": "${corp_secret}",
  "enabled": true
}
EOF
    update_main_config "wechat" "$config_dir/wechat.json"
    success "企业微信集成配置完成"
    echo "INTEGRATION_WECHAT:ok"
}

# Telegram 集成
setup_telegram() {
    local bot_token="$1"
    local config_dir
    config_dir=$(get_config_dir)

    info "配置 Telegram Bot 集成..."
    cat > "$config_dir/telegram.json" <<EOF
{
  "platform": "telegram",
  "bot_token": "${bot_token}",
  "enabled": true
}
EOF
    update_main_config "telegram" "$config_dir/telegram.json"
    success "Telegram 集成配置完成"
    echo "INTEGRATION_TELEGRAM:ok"
}

# 更新主配置文件（整合所有平台）
update_main_config() {
    local platform="$1"
    local platform_config="$2"
    local config_dir
    config_dir=$(get_config_dir)
    local main_config="$config_dir/config.json"

    if command -v python3 &>/dev/null; then
        python3 - <<PYEOF
import json, os

config_file = "${main_config}"
platform_file = "${platform_config}"
platform = "${platform}"

if os.path.exists(config_file):
    with open(config_file) as f:
        config = json.load(f)
else:
    config = {"integrations": {}}

if "integrations" not in config:
    config["integrations"] = {}

with open(platform_file) as f:
    platform_data = json.load(f)

config["integrations"][platform] = platform_data

with open(config_file, "w") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"主配置已更新: {config_file}")
PYEOF
    else
        warn "未安装 python3，跳过主配置合并，平台配置已单独保存"
    fi
}

# 列出已配置的集成
list_integrations() {
    local config_dir
    config_dir=$(get_config_dir)
    local main_config="$config_dir/config.json"

    if [ -f "$main_config" ] && command -v python3 &>/dev/null; then
        python3 - <<PYEOF
import json
with open("${main_config}") as f:
    config = json.load(f)
integrations = config.get("integrations", {})
if integrations:
    for name, data in integrations.items():
        enabled = data.get("enabled", False)
        status = "已启用" if enabled else "已禁用"
        print(f"  {name}: {status}")
else:
    print("  暂无集成配置")
PYEOF
    else
        info "暂无集成配置"
    fi
}

# 命令行入口
case "${1:-list}" in
    feishu)    setup_feishu "${2:-}" "${3:-}" ;;
    qq)        setup_qq "${2:-}" ;;
    wechat)    setup_wechat "${2:-}" "${3:-}" ;;
    telegram)  setup_telegram "${2:-}" ;;
    list)      list_integrations ;;
    *)         echo "用法: $0 {feishu|qq|wechat|telegram|list} [参数...]" ;;
esac
