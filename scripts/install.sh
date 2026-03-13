#!/usr/bin/env bash
# OpenClaw 安装核心脚本
# 支持国际/国内源自动切换，Node.js 检测，进度输出

set -euo pipefail

# ===== 颜色输出 =====
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$(dirname "$SCRIPT_DIR")/logs"
LOG_FILE="$LOG_DIR/install_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$LOG_DIR"

log_and_print() {
    echo "$*" | tee -a "$LOG_FILE"
}

# ===== 进度报告（供 GUI 读取） =====
progress() {
    local step="$1"
    local total="$2"
    local msg="$3"
    echo "PROGRESS:${step}/${total}:${msg}" | tee -a "$LOG_FILE"
}

# ===== 检测网络环境 =====
detect_network() {
    info "正在检测网络环境..."
    local result
    result=$(bash "$SCRIPT_DIR/network_check.sh" 2>/dev/null || echo "cn")
    echo "$result"
}

# ===== 设置 npm 镜像 =====
set_npm_registry() {
    local region="$1"
    if [ "$region" = "cn" ]; then
        info "使用国内 npm 镜像（淘宝源）"
        npm config set registry https://registry.npmmirror.com
    else
        info "使用国际 npm 镜像"
        npm config set registry https://registry.npmjs.org
    fi
}

# ===== 检测 Node.js =====
check_nodejs() {
    progress 1 6 "检测 Node.js 环境"
    if command -v node &>/dev/null; then
        local ver
        ver=$(node --version)
        success "Node.js 已安装: $ver"
        # 检查版本 >= 18
        local major
        major=$(echo "$ver" | sed 's/v//' | cut -d. -f1)
        if [ "$major" -lt 18 ]; then
            warn "Node.js 版本过低（需要 >= 18），将尝试升级"
            install_nodejs "$1"
        fi
    else
        warn "未检测到 Node.js，开始安装..."
        install_nodejs "$1"
    fi
}

# ===== 安装 Node.js =====
install_nodejs() {
    local region="$1"
    progress 2 6 "安装 Node.js"

    local OS
    OS=$(uname -s)

    case "$OS" in
        Darwin)
            if command -v brew &>/dev/null; then
                brew install node
            else
                # 下载官方包
                if [ "$region" = "cn" ]; then
                    local url="https://npmmirror.com/mirrors/node/v20.18.0/node-v20.18.0.pkg"
                else
                    local url="https://nodejs.org/dist/v20.18.0/node-v20.18.0.pkg"
                fi
                info "下载 Node.js: $url"
                curl -L "$url" -o /tmp/nodejs.pkg
                sudo installer -pkg /tmp/nodejs.pkg -target /
            fi
            ;;
        Linux)
            if [ "$region" = "cn" ]; then
                # 使用阿里云 NodeSource 镜像
                curl -fsSL https://npmmirror.com/mirrors/node/v20.18.0/node-v20.18.0-linux-x64.tar.gz -o /tmp/node.tar.gz
                sudo tar -xzf /tmp/node.tar.gz -C /usr/local --strip-components=1
            else
                curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
                sudo apt-get install -y nodejs 2>/dev/null || \
                sudo yum install -y nodejs 2>/dev/null || \
                error "请手动安装 Node.js >= 18"
            fi
            ;;
        MINGW*|MSYS*|CYGWIN*)
            if [ "$region" = "cn" ]; then
                local url="https://npmmirror.com/mirrors/node/v20.18.0/node-v20.18.0-x64.msi"
            else
                local url="https://nodejs.org/dist/v20.18.0/node-v20.18.0-x64.msi"
            fi
            info "请手动安装 Node.js: $url"
            echo "NODE_DOWNLOAD_URL:$url"
            ;;
        *)
            error "不支持的操作系统: $OS"
            exit 1
            ;;
    esac

    success "Node.js 安装完成"
}

# ===== 安装 OpenClaw =====
install_openclaw() {
    local region="$1"
    progress 4 6 "安装 OpenClaw"

    set_npm_registry "$region"

    info "开始安装 openclaw..."

    if npm install -g openclaw 2>&1 | tee -a "$LOG_FILE"; then
        success "OpenClaw 安装成功"
    else
        error "npm 安装失败，尝试备用方式..."
        if [ "$region" = "cn" ]; then
            # 使用官方安装脚本（cnpm 加速方式）
            curl -fsSL https://openclaw.ai/install.sh | bash 2>&1 | tee -a "$LOG_FILE"
        else
            curl -fsSL https://openclaw.ai/install.sh | bash 2>&1 | tee -a "$LOG_FILE"
        fi
    fi
}

# ===== 验证安装 =====
verify_install() {
    progress 5 6 "验证安装"
    if command -v openclaw &>/dev/null; then
        local ver
        ver=$(openclaw --version 2>/dev/null || echo "unknown")
        success "OpenClaw 安装成功，版本: $ver"
        echo "OPENCLAW_VERSION:$ver"
        return 0
    else
        error "OpenClaw 验证失败，请检查日志: $LOG_FILE"
        return 1
    fi
}

# ===== 主流程 =====
main() {
    log_and_print "===== OpenClaw 自动安装工具 ====="
    log_and_print "时间: $(date)"
    log_and_print "系统: $(uname -s) $(uname -m)"
    log_and_print "================================="

    progress 0 6 "开始安装"

    local region
    region=$(detect_network)
    info "网络环境: $region"
    echo "NETWORK_REGION:$region"

    check_nodejs "$region"
    progress 3 6 "Node.js 就绪"

    install_openclaw "$region"
    verify_install
    progress 6 6 "安装完成"
    success "所有步骤完成！"
}

main "$@"
