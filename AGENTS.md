# OpenClaw AutoConfig - AGENTS 配置说明

## 项目概述
全自动安装配置 OpenClaw 的 GUI 工具，基于 Python tkinter + Shell 脚本。

## 目录结构
- `main.py` - GUI 主界面
- `run.sh` - 启动入口
- `scripts/install.sh` - 核心安装逻辑
- `scripts/network_check.sh` - 网络检测
- `scripts/status_check.sh` - 进程状态（输出 JSON）
- `scripts/integrations.sh` - 平台集成配置

## 开发规范
- Shell 脚本统一使用 `set -euo pipefail`
- 进度信息格式：`PROGRESS:step/total:message`（供 GUI 解析）
- 状态检测输出 JSON 格式
- 国内/国际镜像通过 `network_check.sh` 自动判断

## 运行方式
```bash
# GUI 模式
bash run.sh

# 命令行安装
bash scripts/install.sh

# 检查状态
bash scripts/status_check.sh

# 配置集成
bash scripts/integrations.sh feishu <APP_ID> <APP_SECRET>
bash scripts/integrations.sh telegram <BOT_TOKEN>
```

## 代码检查
- Shell: `shellcheck scripts/*.sh`（如已安装）
- Python: `python3 -m py_compile main.py`
