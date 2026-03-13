#!/usr/bin/env python3
"""
OpenClaw 自动配置工具 - GUI 主界面
基于 tkinter（Python 内置，无需额外安装）
支持：全自动安装、进程监控、常用设置、平台集成
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import json
import os
import sys
import time
import re

SCRIPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")

# ===== 主题颜色 =====
COLORS = {
    "bg":        "#1e1e2e",
    "sidebar":   "#181825",
    "card":      "#313244",
    "accent":    "#89b4fa",
    "success":   "#a6e3a1",
    "warning":   "#f9e2af",
    "error":     "#f38ba8",
    "text":      "#cdd6f4",
    "subtext":   "#a6adc8",
    "border":    "#45475a",
    "btn":       "#89b4fa",
    "btn_hover": "#74c7ec",
}


class OpenClawInstaller(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OpenClaw 自动配置工具")
        self.geometry("980x680")
        self.minsize(900, 600)
        self.configure(bg=COLORS["bg"])
        self.resizable(True, True)

        self._install_thread = None
        self._status_timer = None
        self._install_running = False

        self._build_ui()
        self._start_status_poll()

    # ===== 构建 UI =====
    def _build_ui(self):
        # 左侧导航
        sidebar = tk.Frame(self, bg=COLORS["sidebar"], width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        logo = tk.Label(sidebar, text="🐾 OpenClaw", font=("SF Pro", 18, "bold"),
                        bg=COLORS["sidebar"], fg=COLORS["accent"])
        logo.pack(pady=(24, 4))
        subtitle = tk.Label(sidebar, text="自动配置工具", font=("SF Pro", 10),
                            bg=COLORS["sidebar"], fg=COLORS["subtext"])
        subtitle.pack(pady=(0, 24))

        self._pages = {}
        self._nav_btns = {}
        nav_items = [
            ("install",      "⚡  安装"),
            ("status",       "📊  状态监控"),
            ("settings",     "⚙️  常用设置"),
            ("integrations", "🔗  平台集成"),
            ("logs",         "📋  日志"),
        ]

        for page_id, label in nav_items:
            btn = tk.Button(
                sidebar, text=label, anchor="w",
                font=("SF Pro", 12), padx=20,
                bg=COLORS["sidebar"], fg=COLORS["text"],
                activebackground=COLORS["card"],
                activeforeground=COLORS["accent"],
                bd=0, relief="flat", cursor="hand2",
                command=lambda p=page_id: self._show_page(p)
            )
            btn.pack(fill="x", pady=1)
            self._nav_btns[page_id] = btn

        # 主内容区
        self._content = tk.Frame(self, bg=COLORS["bg"])
        self._content.pack(side="left", fill="both", expand=True)

        # 构建各页面
        self._pages["install"]      = self._build_install_page()
        self._pages["status"]       = self._build_status_page()
        self._pages["settings"]     = self._build_settings_page()
        self._pages["integrations"] = self._build_integrations_page()
        self._pages["logs"]         = self._build_logs_page()

        self._show_page("install")

    def _show_page(self, page_id):
        for pid, frame in self._pages.items():
            frame.pack_forget()
            self._nav_btns[pid].configure(bg=COLORS["sidebar"], fg=COLORS["text"])
        self._pages[page_id].pack(fill="both", expand=True)
        self._nav_btns[page_id].configure(bg=COLORS["card"], fg=COLORS["accent"])

    # ===== 安装页面 =====
    def _build_install_page(self):
        frame = tk.Frame(self._content, bg=COLORS["bg"])

        title = tk.Label(frame, text="安装 OpenClaw", font=("SF Pro", 20, "bold"),
                         bg=COLORS["bg"], fg=COLORS["text"])
        title.pack(pady=(32, 4), padx=32, anchor="w")
        desc = tk.Label(frame, text="全自动检测环境、选择最优下载源、完成安装",
                        font=("SF Pro", 12), bg=COLORS["bg"], fg=COLORS["subtext"])
        desc.pack(padx=32, anchor="w")

        # 网络状态卡片
        net_card = self._make_card(frame)
        tk.Label(net_card, text="网络环境", font=("SF Pro", 12, "bold"),
                 bg=COLORS["card"], fg=COLORS["subtext"]).pack(anchor="w")
        self._net_label = tk.Label(net_card, text="点击「开始安装」自动检测",
                                   font=("SF Pro", 13), bg=COLORS["card"], fg=COLORS["text"])
        self._net_label.pack(anchor="w", pady=(4, 0))

        # 进度区域
        prog_card = self._make_card(frame)
        tk.Label(prog_card, text="安装进度", font=("SF Pro", 12, "bold"),
                 bg=COLORS["card"], fg=COLORS["subtext"]).pack(anchor="w")

        self._progress_var = tk.DoubleVar(value=0)
        self._progress_bar = ttk.Progressbar(prog_card, variable=self._progress_var,
                                             maximum=100, length=500, mode="determinate")
        self._progress_bar.pack(fill="x", pady=(8, 4))

        self._progress_label = tk.Label(prog_card, text="等待安装...",
                                        font=("SF Pro", 11), bg=COLORS["card"], fg=COLORS["subtext"])
        self._progress_label.pack(anchor="w")

        # 安装输出
        output_card = self._make_card(frame, pady=0)
        tk.Label(output_card, text="安装输出", font=("SF Pro", 12, "bold"),
                 bg=COLORS["card"], fg=COLORS["subtext"]).pack(anchor="w", pady=(0, 6))
        self._install_output = scrolledtext.ScrolledText(
            output_card, height=10, font=("Menlo", 10),
            bg="#11111b", fg=COLORS["text"], insertbackground=COLORS["text"],
            bd=0, relief="flat", wrap="word"
        )
        self._install_output.pack(fill="both", expand=True)

        # 按钮区
        btn_frame = tk.Frame(frame, bg=COLORS["bg"])
        btn_frame.pack(fill="x", padx=32, pady=16)

        self._install_btn = self._make_btn(btn_frame, "⚡  开始安装", self._start_install)
        self._install_btn.pack(side="left", padx=(0, 12))

        self._stop_btn = self._make_btn(btn_frame, "⏹  停止", self._stop_install,
                                        color=COLORS["error"])
        self._stop_btn.pack(side="left")
        self._stop_btn.configure(state="disabled")

        return frame

    # ===== 状态监控页面 =====
    def _build_status_page(self):
        frame = tk.Frame(self._content, bg=COLORS["bg"])

        title = tk.Label(frame, text="状态监控", font=("SF Pro", 20, "bold"),
                         bg=COLORS["bg"], fg=COLORS["text"])
        title.pack(pady=(32, 4), padx=32, anchor="w")

        card = self._make_card(frame)
        fields = [
            ("安装状态",  "_st_installed"),
            ("运行状态",  "_st_status"),
            ("版本",      "_st_version"),
            ("进程 PID",  "_st_pid"),
            ("配置文件",  "_st_config"),
        ]
        self._status_labels = {}
        for label_text, attr in fields:
            row = tk.Frame(card, bg=COLORS["card"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label_text + "：", width=12, anchor="w",
                     font=("SF Pro", 12), bg=COLORS["card"], fg=COLORS["subtext"]).pack(side="left")
            lbl = tk.Label(row, text="检测中...", anchor="w",
                           font=("SF Pro", 12, "bold"), bg=COLORS["card"], fg=COLORS["text"])
            lbl.pack(side="left", fill="x", expand=True)
            setattr(self, attr, lbl)
            self._status_labels[attr] = lbl

        btn_frame = tk.Frame(frame, bg=COLORS["bg"])
        btn_frame.pack(fill="x", padx=32, pady=8)
        self._make_btn(btn_frame, "🔄  刷新状态", self._refresh_status).pack(side="left", padx=(0,12))
        self._make_btn(btn_frame, "▶  启动 OpenClaw",
                       lambda: self._run_cmd(["openclaw", "start"])).pack(side="left", padx=(0,12))
        self._make_btn(btn_frame, "⏹  停止 OpenClaw",
                       lambda: self._run_cmd(["openclaw", "stop"]),
                       color=COLORS["error"]).pack(side="left")

        return frame

    # ===== 常用设置页面 =====
    def _build_settings_page(self):
        frame = tk.Frame(self._content, bg=COLORS["bg"])

        title = tk.Label(frame, text="常用设置", font=("SF Pro", 20, "bold"),
                         bg=COLORS["bg"], fg=COLORS["text"])
        title.pack(pady=(32, 4), padx=32, anchor="w")

        card = self._make_card(frame)

        settings_items = [
            ("npm 镜像源", "npm_registry", [
                ("国内（淘宝）", "https://registry.npmmirror.com"),
                ("国际（npmjs）", "https://registry.npmjs.org"),
            ]),
        ]

        self._settings_vars = {}

        for label, key, options in settings_items:
            row = tk.Frame(card, bg=COLORS["card"])
            row.pack(fill="x", pady=6)
            tk.Label(row, text=label + "：", width=16, anchor="w",
                     font=("SF Pro", 12), bg=COLORS["card"], fg=COLORS["subtext"]).pack(side="left")
            var = tk.StringVar(value=options[0][1])
            self._settings_vars[key] = var
            for opt_label, opt_val in options:
                rb = tk.Radiobutton(row, text=opt_label, variable=var, value=opt_val,
                                    font=("SF Pro", 11), bg=COLORS["card"],
                                    fg=COLORS["text"], selectcolor=COLORS["bg"],
                                    activebackground=COLORS["card"])
                rb.pack(side="left", padx=8)

        # 开机自启
        self._autostart_var = tk.BooleanVar(value=False)
        autostart_row = tk.Frame(card, bg=COLORS["card"])
        autostart_row.pack(fill="x", pady=6)
        tk.Label(autostart_row, text="开机自启：", width=16, anchor="w",
                 font=("SF Pro", 12), bg=COLORS["card"], fg=COLORS["subtext"]).pack(side="left")
        tk.Checkbutton(autostart_row, text="启用", variable=self._autostart_var,
                       font=("SF Pro", 11), bg=COLORS["card"], fg=COLORS["text"],
                       selectcolor=COLORS["bg"], activebackground=COLORS["card"]).pack(side="left")

        self._make_btn(frame, "💾  保存设置", self._save_settings).pack(anchor="w", padx=32, pady=12)

        return frame

    # ===== 平台集成页面 =====
    def _build_integrations_page(self):
        frame = tk.Frame(self._content, bg=COLORS["bg"])

        title = tk.Label(frame, text="平台集成", font=("SF Pro", 20, "bold"),
                         bg=COLORS["bg"], fg=COLORS["text"])
        title.pack(pady=(32, 4), padx=32, anchor="w")
        desc = tk.Label(frame, text="配置 OpenClaw 与聊天软件的集成",
                        font=("SF Pro", 12), bg=COLORS["bg"], fg=COLORS["subtext"])
        desc.pack(padx=32, anchor="w", pady=(0, 8))

        # Tab 切换
        notebook = ttk.Notebook(frame)
        notebook.pack(fill="both", expand=True, padx=32, pady=8)

        self._integration_entries = {}

        platforms = [
            ("飞书",   "feishu",   [("App ID", "app_id"), ("App Secret", "app_secret")]),
            ("QQ",     "qq",       [("Bot Token", "bot_token")]),
            ("企业微信", "wechat", [("Corp ID", "corp_id"), ("Corp Secret", "corp_secret")]),
            ("Telegram", "telegram", [("Bot Token", "bot_token")]),
        ]

        for plat_name, plat_id, fields in platforms:
            tab = tk.Frame(notebook, bg=COLORS["bg"], padx=20, pady=20)
            notebook.add(tab, text=plat_name)
            self._integration_entries[plat_id] = {}

            for field_label, field_key in fields:
                row = tk.Frame(tab, bg=COLORS["bg"])
                row.pack(fill="x", pady=6)
                tk.Label(row, text=field_label + "：", width=14, anchor="w",
                         font=("SF Pro", 12), bg=COLORS["bg"], fg=COLORS["subtext"]).pack(side="left")
                entry = tk.Entry(row, font=("Menlo", 12), bg=COLORS["card"],
                                 fg=COLORS["text"], insertbackground=COLORS["text"],
                                 bd=0, relief="flat")
                entry.pack(side="left", fill="x", expand=True, ipady=6, ipadx=8)
                self._integration_entries[plat_id][field_key] = entry

            self._make_btn(tab, f"✅  保存{plat_name}配置",
                           lambda p=plat_id: self._save_integration(p)).pack(anchor="w", pady=12)

        return frame

    # ===== 日志页面 =====
    def _build_logs_page(self):
        frame = tk.Frame(self._content, bg=COLORS["bg"])

        title = tk.Label(frame, text="安装日志", font=("SF Pro", 20, "bold"),
                         bg=COLORS["bg"], fg=COLORS["text"])
        title.pack(pady=(32, 4), padx=32, anchor="w")

        self._log_text = scrolledtext.ScrolledText(
            frame, font=("Menlo", 10), bg="#11111b", fg=COLORS["text"],
            insertbackground=COLORS["text"], bd=0, relief="flat", wrap="word"
        )
        self._log_text.pack(fill="both", expand=True, padx=32, pady=8)

        btn_frame = tk.Frame(frame, bg=COLORS["bg"])
        btn_frame.pack(fill="x", padx=32, pady=8)
        self._make_btn(btn_frame, "🔄  刷新日志", self._load_logs).pack(side="left", padx=(0, 12))
        self._make_btn(btn_frame, "🗑  清空日志",
                       lambda: self._log_text.delete("1.0", "end"),
                       color=COLORS["warning"]).pack(side="left")

        self._load_logs()
        return frame

    # ===== 工具方法 =====
    def _make_card(self, parent, pady=8):
        card = tk.Frame(parent, bg=COLORS["card"], bd=0, relief="flat")
        card.pack(fill="x", padx=32, pady=pady, ipadx=16, ipady=12)
        return card

    def _make_btn(self, parent, text, command, color=None):
        color = color or COLORS["btn"]
        btn = tk.Button(
            parent, text=text, command=command,
            font=("SF Pro", 12, "bold"),
            bg=color, fg=COLORS["bg"],
            activebackground=COLORS["btn_hover"], activeforeground=COLORS["bg"],
            bd=0, relief="flat", cursor="hand2", padx=16, pady=8
        )
        return btn

    def _append_output(self, text, tag=None):
        self._install_output.configure(state="normal")
        self._install_output.insert("end", text + "\n")
        self._install_output.see("end")
        self._install_output.configure(state="disabled")

    # ===== 安装逻辑 =====
    def _start_install(self):
        if self._install_running:
            return
        self._install_running = True
        self._install_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._install_output.configure(state="normal")
        self._install_output.delete("1.0", "end")
        self._install_output.configure(state="disabled")
        self._progress_var.set(0)
        self._progress_label.configure(text="正在安装...")

        self._install_thread = threading.Thread(target=self._run_install, daemon=True)
        self._install_thread.start()

    def _stop_install(self):
        self._install_running = False
        self._install_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")
        self._progress_label.configure(text="已停止")
        self._append_output("[已手动停止安装]")

    def _run_install(self):
        script = os.path.join(SCRIPT_DIR, "install.sh")
        if not os.path.exists(script):
            self.after(0, lambda: self._append_output(f"[错误] 找不到安装脚本: {script}"))
            self._install_running = False
            return

        try:
            proc = subprocess.Popen(
                ["bash", script],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )
            for line in proc.stdout:
                if not self._install_running:
                    proc.terminate()
                    break
                line = line.rstrip()
                self.after(0, lambda l=line: self._handle_install_line(l))
            proc.wait()
        except Exception as e:
            self.after(0, lambda: self._append_output(f"[异常] {e}"))
        finally:
            self._install_running = False
            self.after(0, lambda: self._install_btn.configure(state="normal"))
            self.after(0, lambda: self._stop_btn.configure(state="disabled"))

    def _handle_install_line(self, line):
        self._append_output(line)
        # 解析进度
        m = re.match(r"PROGRESS:(\d+)/(\d+):(.+)", line)
        if m:
            step, total, msg = int(m.group(1)), int(m.group(2)), m.group(3)
            pct = (step / total) * 100
            self._progress_var.set(pct)
            self._progress_label.configure(text=f"步骤 {step}/{total}: {msg}")
        elif line.startswith("NETWORK_REGION:"):
            region = line.split(":")[1]
            region_text = "国内网络（使用国内镜像）" if region == "cn" else "国际网络"
            self._net_label.configure(text=region_text,
                                      fg=COLORS["warning"] if region == "cn" else COLORS["success"])

    # ===== 状态监控 =====
    def _start_status_poll(self):
        self._refresh_status()
        self._status_timer = self.after(10000, self._start_status_poll)

    def _refresh_status(self):
        def do_check():
            script = os.path.join(SCRIPT_DIR, "status_check.sh")
            try:
                result = subprocess.run(["bash", script], capture_output=True, text=True, timeout=5)
                data = json.loads(result.stdout.strip())
                self.after(0, lambda: self._update_status_ui(data))
            except Exception as e:
                self.after(0, lambda: self._update_status_ui(None))
        threading.Thread(target=do_check, daemon=True).start()

    def _update_status_ui(self, data):
        if not data:
            for attr in ["_st_installed", "_st_status", "_st_version", "_st_pid", "_st_config"]:
                getattr(self, attr).configure(text="检测失败", fg=COLORS["error"])
            return
        installed = data.get("installed", False)
        status    = data.get("status", "unknown")
        version   = data.get("version", "unknown")
        pid       = data.get("pid", "—")
        config    = data.get("config", "—") or "—"

        self._st_installed.configure(
            text="已安装 ✓" if installed else "未安装",
            fg=COLORS["success"] if installed else COLORS["error"])
        self._st_status.configure(
            text="运行中 ▶" if status == "running" else "已停止",
            fg=COLORS["success"] if status == "running" else COLORS["subtext"])
        self._st_version.configure(text=version, fg=COLORS["text"])
        self._st_pid.configure(text=pid or "—", fg=COLORS["text"])
        self._st_config.configure(text=config, fg=COLORS["text"])

    def _run_cmd(self, cmd):
        def do_run():
            try:
                subprocess.run(cmd, check=True)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("错误", str(e)))
        threading.Thread(target=do_run, daemon=True).start()

    # ===== 设置保存 =====
    def _save_settings(self):
        registry = self._settings_vars["npm_registry"].get()
        try:
            subprocess.run(["npm", "config", "set", "registry", registry], check=True)
            messagebox.showinfo("保存成功", f"npm 镜像已设置为：\n{registry}")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    # ===== 集成配置保存 =====
    def _save_integration(self, platform):
        fields = self._integration_entries.get(platform, {})
        args = [fields[k].get().strip() for k in fields]

        if not all(args):
            messagebox.showwarning("提示", "请填写所有必填字段")
            return

        script = os.path.join(SCRIPT_DIR, "integrations.sh")
        cmd = ["bash", script, platform] + args

        def do_save():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self.after(0, lambda: messagebox.showinfo("成功", f"{platform} 集成配置已保存"))
                else:
                    err = result.stderr or result.stdout
                    self.after(0, lambda: messagebox.showerror("失败", err))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("异常", str(e)))
        threading.Thread(target=do_save, daemon=True).start()

    # ===== 加载日志 =====
    def _load_logs(self):
        self._log_text.configure(state="normal")
        self._log_text.delete("1.0", "end")
        os.makedirs(LOG_DIR, exist_ok=True)
        log_files = sorted(
            [f for f in os.listdir(LOG_DIR) if f.endswith(".log")],
            reverse=True
        )
        if log_files:
            latest = os.path.join(LOG_DIR, log_files[0])
            try:
                with open(latest, "r", encoding="utf-8") as f:
                    content = f.read()
                self._log_text.insert("1.0", content)
                self._log_text.see("end")
            except Exception as e:
                self._log_text.insert("1.0", f"读取日志失败: {e}")
        else:
            self._log_text.insert("1.0", "暂无日志")
        self._log_text.configure(state="disabled")

    def destroy(self):
        if self._status_timer:
            self.after_cancel(self._status_timer)
        super().destroy()


if __name__ == "__main__":
    app = OpenClawInstaller()
    app.mainloop()
