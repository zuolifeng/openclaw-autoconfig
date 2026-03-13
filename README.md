# OpenClaw 自动配置工具

全自动安装、配置 [OpenClaw](https://openclaw.ai/)，支持国内外网络环境自动切换，内置 GUI 界面。

## 功能特性

- **一键安装**：自动检测 Node.js 环境，按需安装依赖
- **网络自适应**：自动检测网络环境，国内自动切换淘宝 npm 镜像
- **可视化进度**：GUI 界面实时显示安装进度和日志
- **进程监控**：查看 OpenClaw 运行状态、版本、PID
- **常用设置**：npm 镜像源切换、开机自启等
- **平台集成**：飞书、QQ、企业微信、Telegram 一键配置
- **全平台支持**：macOS / Linux / Windows（WSL）

## 快速开始

### 方式一：GUI 界面（推荐）

```bash
bash run.sh
```

### 方式二：纯命令行安装

```bash
bash scripts/install.sh
```

## 目录结构

```
.
├── main.py                 # GUI 主界面（Python tkinter）
├── run.sh                  # 启动脚本
├── scripts/
│   ├── install.sh          # 核心安装脚本
│   ├── network_check.sh    # 网络环境检测
│   ├── status_check.sh     # 进程状态检测
│   └── integrations.sh     # 平台集成配置
├── logs/                   # 安装日志目录
└── config/                 # 本地配置目录
```

## 系统要求

| 依赖 | 版本要求 |
|------|----------|
| Python | >= 3.8 |
| Node.js | >= 18（会自动安装） |
| curl | 任意版本 |

## 平台集成配置

支持以下平台：

| 平台 | 所需信息 |
|------|----------|
| 飞书 | App ID + App Secret |
| QQ 机器人 | Bot Token |
| 企业微信 | Corp ID + Corp Secret |
| Telegram | Bot Token |

在 GUI「平台集成」标签页中填写对应信息即可自动保存配置。

## 国内/国际源说明

安装时自动检测是否能访问 `registry.npmjs.org`：
- 可访问 → 使用国际源
- 不可访问 → 自动切换淘宝 npm 镜像 `registry.npmmirror.com`

## 常见问题

**GUI 无法启动？**
```bash
# 安装 tkinter（Ubuntu/Debian）
sudo apt-get install python3-tk
# macOS
brew install python-tk
```

**Node.js 安装失败？**
手动下载安装：
- 国际：https://nodejs.org/
- 国内：https://npmmirror.com/mirrors/node/
