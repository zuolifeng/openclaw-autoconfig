#!/usr/bin/env bash
# 本地打包脚本 - 在当前平台打包 OpenClaw AutoConfig
set -euo pipefail

BLUE='\033[0;34m'; GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$PROJECT_DIR/dist"
BUILD_DIR="$PROJECT_DIR/build"
VERSION="${1:-1.0.0}"

OS=$(uname -s)
ARCH=$(uname -m)

case "$OS" in
    Darwin) PLATFORM="macos" ;;
    Linux)  PLATFORM="linux" ;;
    MINGW*|MSYS*|CYGWIN*) PLATFORM="windows" ;;
    *) error "Unsupported OS: $OS" ;;
esac

case "$ARCH" in
    x86_64|amd64) ARCH_NAME="amd64" ;;
    arm64|aarch64) ARCH_NAME="arm64" ;;
    *) ARCH_NAME="$ARCH" ;;
esac

ARTIFACT_NAME="OpenClawAutoConfig-v${VERSION}-${PLATFORM}-${ARCH_NAME}"

info "Platform: $PLATFORM ($ARCH_NAME)"
info "Version:  $VERSION"
info "Output:   $ARTIFACT_NAME"

# 检查 python3
command -v python3 &>/dev/null || error "python3 not found"

# 安装 pyinstaller
if ! python3 -m PyInstaller --version &>/dev/null; then
    info "Installing PyInstaller..."
    pip3 install pyinstaller
fi

# 清理旧文件
rm -rf "$DIST_DIR" "$BUILD_DIR"

# 打包
info "Building with PyInstaller..."
python3 -m PyInstaller "$PROJECT_DIR/openclaw_autoconfig.spec" \
    --distpath "$DIST_DIR" \
    --workpath "$BUILD_DIR" \
    --clean \
    --noconfirm

# 归档
info "Creating archive..."
mkdir -p "$DIST_DIR/release"

case "$PLATFORM" in
    macos)
        if [ -d "$DIST_DIR/OpenClawAutoConfig.app" ]; then
            cd "$DIST_DIR"
            zip -r "release/${ARTIFACT_NAME}.zip" "OpenClawAutoConfig.app"
        else
            cd "$DIST_DIR"
            zip -r "release/${ARTIFACT_NAME}.zip" "OpenClawAutoConfig"
        fi
        ;;
    linux)
        cd "$DIST_DIR"
        chmod +x OpenClawAutoConfig
        tar -czf "release/${ARTIFACT_NAME}.tar.gz" OpenClawAutoConfig
        ;;
    windows)
        cd "$DIST_DIR"
        if command -v zip &>/dev/null; then
            zip "release/${ARTIFACT_NAME}.zip" OpenClawAutoConfig.exe
        else
            info "zip not available, file at: $DIST_DIR/OpenClawAutoConfig.exe"
            cp OpenClawAutoConfig.exe "release/${ARTIFACT_NAME}.exe"
        fi
        ;;
esac

success "Build complete!"
echo ""
info "Artifacts in: $DIST_DIR/release/"
ls -lh "$DIST_DIR/release/"
