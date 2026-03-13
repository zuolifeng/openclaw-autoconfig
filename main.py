#!/usr/bin/env python3
"""
OpenClaw AutoConfig Tool - GUI Main Interface
Based on tkinter (Python built-in, no extra installation needed)
Features: Auto install, process monitor, settings, integrations, multi-language
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
LOCALES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locales")

# ===== Theme Colors =====
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


class LanguageManager:
    """Multi-language support manager"""
    def __init__(self):
        self._current_lang = "zh"
        self._texts = {}
        self._load_language("zh")

    def _load_language(self, lang):
        lang_file = os.path.join(LOCALES_DIR, f"{lang}.json")
        try:
            with open(lang_file, "r", encoding="utf-8") as f:
                self._texts = json.load(f)
            self._current_lang = lang
        except Exception as e:
            print(f"[WARN] Failed to load language file: {e}")
            self._texts = {}

    def get(self, key, default=None):
        return self._texts.get(key, default or key)

    def set_language(self, lang):
        if lang != self._current_lang:
            self._load_language(lang)

    @property
    def current_lang(self):
        return self._current_lang


class OpenClawInstaller(tk.Tk):
    def __init__(self):
        super().__init__()
        self._lang = LanguageManager()
        self.title(self._lang.get("app_title", "OpenClaw AutoConfig"))
        self.geometry("980x680")
        self.minsize(900, 600)
        self.configure(bg=COLORS["bg"])
        self.resizable(True, True)

        self._install_thread = None
        self._status_timer = None
        self._install_running = False

        self._build_ui()
        self._start_status_poll()

    # ===== Build UI =====
    def _build_ui(self):
        # Left sidebar
        sidebar = tk.Frame(self, bg=COLORS["sidebar"], width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        logo = tk.Label(sidebar, text="🐾 OpenClaw", font=("SF Pro", 18, "bold"),
                        bg=COLORS["sidebar"], fg=COLORS["accent"])
        logo.pack(pady=(24, 4))
        self._subtitle_label = tk.Label(sidebar, text=self._lang.get("app_title", "AutoConfig"),
                            font=("SF Pro", 10), bg=COLORS["sidebar"], fg=COLORS["subtext"])
        self._subtitle_label.pack(pady=(0, 16))

        # Language switch
        lang_frame = tk.Frame(sidebar, bg=COLORS["sidebar"])
        lang_frame.pack(pady=(0, 16))
        tk.Label(lang_frame, text="🌐", font=("SF Pro", 11),
                 bg=COLORS["sidebar"], fg=COLORS["subtext"]).pack(side="left", padx=(0, 4))
        self._lang_btn_zh = tk.Button(
            lang_frame, text="中文", command=lambda: self._switch_language("zh"),
            font=("SF Pro", 10), bg=COLORS["card"] if self._lang.current_lang == "zh" else COLORS["sidebar"],
            fg=COLORS["accent"] if self._lang.current_lang == "zh" else COLORS["subtext"],
            bd=0, relief="flat", cursor="hand2", padx=8
        )
        self._lang_btn_zh.pack(side="left", padx=2)
        self._lang_btn_en = tk.Button(
            lang_frame, text="EN", command=lambda: self._switch_language("en"),
            font=("SF Pro", 10), bg=COLORS["card"] if self._lang.current_lang == "en" else COLORS["sidebar"],
            fg=COLORS["accent"] if self._lang.current_lang == "en" else COLORS["subtext"],
            bd=0, relief="flat", cursor="hand2", padx=8
        )
        self._lang_btn_en.pack(side="left", padx=2)

        self._pages = {}
        self._nav_btns = {}
        nav_items = [
            ("install",      "nav_install"),
            ("status",       "nav_status"),
            ("settings",     "nav_settings"),
            ("integrations", "nav_integrations"),
            ("skills",       "nav_skills"),
            ("logs",         "nav_logs"),
        ]

        for page_id, lang_key in nav_items:
            btn = tk.Button(
                sidebar, text=self._lang.get(lang_key, page_id), anchor="w",
                font=("SF Pro", 12), padx=20,
                bg=COLORS["sidebar"], fg=COLORS["text"],
                activebackground=COLORS["card"],
                activeforeground=COLORS["accent"],
                bd=0, relief="flat", cursor="hand2",
                command=lambda p=page_id: self._show_page(p)
            )
            btn.pack(fill="x", pady=1)
            self._nav_btns[page_id] = btn

        # Main content area
        self._content = tk.Frame(self, bg=COLORS["bg"])
        self._content.pack(side="left", fill="both", expand=True)

        # Build all pages
        self._pages["install"]      = self._build_install_page()
        self._pages["status"]       = self._build_status_page()
        self._pages["settings"]     = self._build_settings_page()
        self._pages["integrations"] = self._build_integrations_page()
        self._pages["skills"]       = self._build_skills_page()
        self._pages["logs"]         = self._build_logs_page()

        self._show_page("install")

    def _switch_language(self, lang):
        if lang == self._lang.current_lang:
            return
        self._lang.set_language(lang)
        # Update language button styles
        self._lang_btn_zh.configure(
            bg=COLORS["card"] if lang == "zh" else COLORS["sidebar"],
            fg=COLORS["accent"] if lang == "zh" else COLORS["subtext"]
        )
        self._lang_btn_en.configure(
            bg=COLORS["card"] if lang == "en" else COLORS["sidebar"],
            fg=COLORS["accent"] if lang == "en" else COLORS["subtext"]
        )
        # Rebuild UI with new language
        for page_id in list(self._pages.keys()):
            self._pages[page_id].destroy()
        self._nav_btns.clear()
        # Rebuild sidebar buttons
        for widget in self._content.winfo_children():
            widget.destroy()
        # Rebuild navigation
        nav_items = [
            ("install",      "nav_install"),
            ("status",       "nav_status"),
            ("settings",     "nav_settings"),
            ("integrations", "nav_integrations"),
            ("skills",       "nav_skills"),
            ("logs",         "nav_logs"),
        ]
        sidebar = self._nav_btns.get("install").master if "install" in self._nav_btns else None
        # Rebuild pages
        self._pages["install"]      = self._build_install_page()
        self._pages["status"]       = self._build_status_page()
        self._pages["settings"]     = self._build_settings_page()
        self._pages["integrations"] = self._build_integrations_page()
        self._pages["skills"]       = self._build_skills_page()
        self._pages["logs"]         = self._build_logs_page()
        # Update nav buttons text
        for page_id, lang_key in nav_items:
            if page_id in self._nav_btns:
                self._nav_btns[page_id].configure(text=self._lang.get(lang_key, page_id))
        self._subtitle_label.configure(text=self._lang.get("app_title", "AutoConfig"))
        self._show_page("install")

    def _show_page(self, page_id):
        for pid, frame in self._pages.items():
            frame.pack_forget()
            if pid in self._nav_btns:
                self._nav_btns[pid].configure(bg=COLORS["sidebar"], fg=COLORS["text"])
        self._pages[page_id].pack(fill="both", expand=True)
        if page_id in self._nav_btns:
            self._nav_btns[page_id].configure(bg=COLORS["card"], fg=COLORS["accent"])

    # ===== Install Page =====
    def _build_install_page(self):
        frame = tk.Frame(self._content, bg=COLORS["bg"])

        title = tk.Label(frame, text=self._lang.get("install_title", "Install OpenClaw"),
                         font=("SF Pro", 20, "bold"), bg=COLORS["bg"], fg=COLORS["text"])
        title.pack(pady=(32, 4), padx=32, anchor="w")
        desc = tk.Label(frame, text=self._lang.get("install_desc", "Auto-detect and install"),
                        font=("SF Pro", 12), bg=COLORS["bg"], fg=COLORS["subtext"])
        desc.pack(padx=32, anchor="w")

        # Network status card
        net_card = self._make_card(frame)
        tk.Label(net_card, text=self._lang.get("network_env", "Network Environment"),
                 font=("SF Pro", 12, "bold"), bg=COLORS["card"], fg=COLORS["subtext"]).pack(anchor="w")
        self._net_label = tk.Label(net_card, text=self._lang.get("network_detect_hint", "Click to detect"),
                                   font=("SF Pro", 13), bg=COLORS["card"], fg=COLORS["text"])
        self._net_label.pack(anchor="w", pady=(4, 0))

        # Progress area
        prog_card = self._make_card(frame)
        tk.Label(prog_card, text=self._lang.get("install_progress", "Progress"),
                 font=("SF Pro", 12, "bold"), bg=COLORS["card"], fg=COLORS["subtext"]).pack(anchor="w")

        self._progress_var = tk.DoubleVar(value=0)
        self._progress_bar = ttk.Progressbar(prog_card, variable=self._progress_var,
                                             maximum=100, length=500, mode="determinate")
        self._progress_bar.pack(fill="x", pady=(8, 4))

        self._progress_label = tk.Label(prog_card, text=self._lang.get("waiting_install", "Waiting..."),
                                        font=("SF Pro", 11), bg=COLORS["card"], fg=COLORS["subtext"])
        self._progress_label.pack(anchor="w")

        # Install output
        output_card = self._make_card(frame, pady=0)
        tk.Label(output_card, text=self._lang.get("install_output", "Output"),
                 font=("SF Pro", 12, "bold"), bg=COLORS["card"], fg=COLORS["subtext"]).pack(anchor="w", pady=(0, 6))
        self._install_output = scrolledtext.ScrolledText(
            output_card, height=10, font=("Menlo", 10),
            bg="#11111b", fg=COLORS["text"], insertbackground=COLORS["text"],
            bd=0, relief="flat", wrap="word"
        )
        self._install_output.pack(fill="both", expand=True)

        # Buttons
        btn_frame = tk.Frame(frame, bg=COLORS["bg"])
        btn_frame.pack(fill="x", padx=32, pady=16)

        self._install_btn = self._make_btn(btn_frame, self._lang.get("btn_start_install", "Start Install"), self._start_install)
        self._install_btn.pack(side="left", padx=(0, 12))

        self._stop_btn = self._make_btn(btn_frame, self._lang.get("btn_stop", "Stop"), self._stop_install,
                                        color=COLORS["error"])
        self._stop_btn.pack(side="left")
        self._stop_btn.configure(state="disabled")

        return frame

    # ===== Status Page =====
    def _build_status_page(self):
        frame = tk.Frame(self._content, bg=COLORS["bg"])

        title = tk.Label(frame, text=self._lang.get("status_title", "Status Monitor"),
                         font=("SF Pro", 20, "bold"), bg=COLORS["bg"], fg=COLORS["text"])
        title.pack(pady=(32, 4), padx=32, anchor="w")

        card = self._make_card(frame)
        fields = [
            ("status_installed",  "_st_installed"),
            ("status_running",    "_st_status"),
            ("status_version",    "_st_version"),
            ("status_pid",        "_st_pid"),
            ("status_config",     "_st_config"),
        ]
        self._status_labels = {}
        for lang_key, attr in fields:
            row = tk.Frame(card, bg=COLORS["card"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=self._lang.get(lang_key, lang_key) + "：", width=14, anchor="w",
                     font=("SF Pro", 12), bg=COLORS["card"], fg=COLORS["subtext"]).pack(side="left")
            lbl = tk.Label(row, text=self._lang.get("status_detecting", "Detecting..."), anchor="w",
                           font=("SF Pro", 12, "bold"), bg=COLORS["card"], fg=COLORS["text"])
            lbl.pack(side="left", fill="x", expand=True)
            setattr(self, attr, lbl)
            self._status_labels[attr] = lbl

        btn_frame = tk.Frame(frame, bg=COLORS["bg"])
        btn_frame.pack(fill="x", padx=32, pady=8)
        self._make_btn(btn_frame, self._lang.get("btn_refresh", "Refresh"), self._refresh_status).pack(side="left", padx=(0,12))
        self._make_btn(btn_frame, self._lang.get("btn_start", "Start"),
                       lambda: self._run_cmd(["openclaw", "start"])).pack(side="left", padx=(0,12))
        self._make_btn(btn_frame, self._lang.get("btn_stop_service", "Stop"),
                       lambda: self._run_cmd(["openclaw", "stop"]),
                       color=COLORS["error"]).pack(side="left")

        return frame

    # ===== Settings Page =====
    def _build_settings_page(self):
        frame = tk.Frame(self._content, bg=COLORS["bg"])

        title = tk.Label(frame, text=self._lang.get("settings_title", "Settings"),
                         font=("SF Pro", 20, "bold"), bg=COLORS["bg"], fg=COLORS["text"])
        title.pack(pady=(32, 4), padx=32, anchor="w")

        card = self._make_card(frame)

        settings_items = [
            ("settings_npm_registry", "npm_registry", [
                ("settings_cn_taobao", "https://registry.npmmirror.com"),
                ("settings_global_npmjs", "https://registry.npmjs.org"),
            ]),
        ]

        self._settings_vars = {}

        for lang_key, key, options in settings_items:
            row = tk.Frame(card, bg=COLORS["card"])
            row.pack(fill="x", pady=6)
            tk.Label(row, text=self._lang.get(lang_key, key) + "：", width=18, anchor="w",
                     font=("SF Pro", 12), bg=COLORS["card"], fg=COLORS["subtext"]).pack(side="left")
            var = tk.StringVar(value=options[0][1])
            self._settings_vars[key] = var
            for opt_lang_key, opt_val in options:
                rb = tk.Radiobutton(row, text=self._lang.get(opt_lang_key, opt_val), variable=var, value=opt_val,
                                    font=("SF Pro", 11), bg=COLORS["card"],
                                    fg=COLORS["text"], selectcolor=COLORS["bg"],
                                    activebackground=COLORS["card"])
                rb.pack(side="left", padx=8)

        # Auto-start
        self._autostart_var = tk.BooleanVar(value=False)
        autostart_row = tk.Frame(card, bg=COLORS["card"])
        autostart_row.pack(fill="x", pady=6)
        tk.Label(autostart_row, text=self._lang.get("settings_autostart", "Auto-start") + "：", width=18, anchor="w",
                 font=("SF Pro", 12), bg=COLORS["card"], fg=COLORS["subtext"]).pack(side="left")
        tk.Checkbutton(autostart_row, text=self._lang.get("settings_enable", "Enable"), variable=self._autostart_var,
                       font=("SF Pro", 11), bg=COLORS["card"], fg=COLORS["text"],
                       selectcolor=COLORS["bg"], activebackground=COLORS["card"]).pack(side="left")

        self._make_btn(frame, self._lang.get("btn_save_settings", "Save Settings"), self._save_settings).pack(anchor="w", padx=32, pady=12)

        return frame

    # ===== Integrations Page =====
    def _build_integrations_page(self):
        frame = tk.Frame(self._content, bg=COLORS["bg"])

        title = tk.Label(frame, text=self._lang.get("integrations_title", "Integrations"),
                         font=("SF Pro", 20, "bold"), bg=COLORS["bg"], fg=COLORS["text"])
        title.pack(pady=(32, 4), padx=32, anchor="w")
        desc = tk.Label(frame, text=self._lang.get("integrations_desc", "Configure integrations"),
                        font=("SF Pro", 12), bg=COLORS["bg"], fg=COLORS["subtext"])
        desc.pack(padx=32, anchor="w", pady=(0, 8))

        # Tab switch
        notebook = ttk.Notebook(frame)
        notebook.pack(fill="both", expand=True, padx=32, pady=8)

        self._integration_entries = {}

        platforms = [
            ("tab_feishu",   "feishu",   [("field_app_id", "app_id"), ("field_app_secret", "app_secret")]),
            ("tab_qq",       "qq",       [("field_bot_token", "bot_token")]),
            ("tab_wechat",   "wechat",   [("field_corp_id", "corp_id"), ("field_corp_secret", "corp_secret")]),
            ("tab_telegram", "telegram", [("field_bot_token", "bot_token")]),
        ]

        for plat_lang_key, plat_id, fields in platforms:
            tab = tk.Frame(notebook, bg=COLORS["bg"], padx=20, pady=20)
            notebook.add(tab, text=self._lang.get(plat_lang_key, plat_id))
            self._integration_entries[plat_id] = {}

            for field_lang_key, field_key in fields:
                row = tk.Frame(tab, bg=COLORS["bg"])
                row.pack(fill="x", pady=6)
                tk.Label(row, text=self._lang.get(field_lang_key, field_key) + "：", width=14, anchor="w",
                         font=("SF Pro", 12), bg=COLORS["bg"], fg=COLORS["subtext"]).pack(side="left")
                entry = tk.Entry(row, font=("Menlo", 12), bg=COLORS["card"],
                                 fg=COLORS["text"], insertbackground=COLORS["text"],
                                 bd=0, relief="flat")
                entry.pack(side="left", fill="x", expand=True, ipady=6, ipadx=8)
                self._integration_entries[plat_id][field_key] = entry

            self._make_btn(tab, self._lang.get("btn_save_config", "Save"),
                           lambda p=plat_id: self._save_integration(p)).pack(anchor="w", pady=12)

        return frame

    # ===== Skills Page =====
    def _build_skills_page(self):
        frame = tk.Frame(self._content, bg=COLORS["bg"])

        title = tk.Label(frame, text=self._lang.get("skills_title", "Skills Guide"),
                         font=("SF Pro", 20, "bold"), bg=COLORS["bg"], fg=COLORS["text"])
        title.pack(pady=(32, 4), padx=32, anchor="w")
        desc = tk.Label(frame, text=self._lang.get("skills_desc", "OpenClaw AI capabilities"),
                        font=("SF Pro", 12), bg=COLORS["bg"], fg=COLORS["subtext"])
        desc.pack(padx=32, anchor="w", pady=(0, 12))

        # Skills list
        skills = [
            ("skill_email",     "skill_email_desc"),
            ("skill_calendar",  "skill_calendar_desc"),
            ("skill_files",     "skill_files_desc"),
            ("skill_commands",  "skill_commands_desc"),
            ("skill_search",    "skill_search_desc"),
            ("skill_notes",     "skill_notes_desc"),
            ("skill_custom",    "skill_custom_desc"),
        ]

        skills_frame = tk.Frame(frame, bg=COLORS["bg"])
        skills_frame.pack(fill="both", expand=True, padx=32, pady=8)

        for i, (title_key, desc_key) in enumerate(skills):
            skill_card = tk.Frame(skills_frame, bg=COLORS["card"], bd=0)
            skill_card.pack(fill="x", pady=4, ipadx=16, ipady=12)

            # Skill title
            tk.Label(skill_card, text=self._lang.get(title_key, title_key),
                     font=("SF Pro", 13, "bold"), bg=COLORS["card"], fg=COLORS["accent"]).pack(anchor="w")
            # Skill description
            tk.Label(skill_card, text=self._lang.get(desc_key, desc_key),
                     font=("SF Pro", 11), bg=COLORS["card"], fg=COLORS["subtext"],
                     wraplength=700, justify="left").pack(anchor="w", pady=(4, 0))

        return frame

    # ===== Logs Page =====
    def _build_logs_page(self):
        frame = tk.Frame(self._content, bg=COLORS["bg"])

        title = tk.Label(frame, text=self._lang.get("logs_title", "Logs"),
                         font=("SF Pro", 20, "bold"), bg=COLORS["bg"], fg=COLORS["text"])
        title.pack(pady=(32, 4), padx=32, anchor="w")

        self._log_text = scrolledtext.ScrolledText(
            frame, font=("Menlo", 10), bg="#11111b", fg=COLORS["text"],
            insertbackground=COLORS["text"], bd=0, relief="flat", wrap="word"
        )
        self._log_text.pack(fill="both", expand=True, padx=32, pady=8)

        btn_frame = tk.Frame(frame, bg=COLORS["bg"])
        btn_frame.pack(fill="x", padx=32, pady=8)
        self._make_btn(btn_frame, self._lang.get("btn_refresh_logs", "Refresh"), self._load_logs).pack(side="left", padx=(0, 12))
        self._make_btn(btn_frame, self._lang.get("btn_clear_logs", "Clear"),
                       lambda: self._log_text.delete("1.0", "end"),
                       color=COLORS["warning"]).pack(side="left")

        self._load_logs()
        return frame

    # ===== Utility Methods =====
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

    # ===== Install Logic =====
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
        self._progress_label.configure(text="...")

        self._install_thread = threading.Thread(target=self._run_install, daemon=True)
        self._install_thread.start()

    def _stop_install(self):
        self._install_running = False
        self._install_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")
        self._progress_label.configure(text=self._lang.get("install_stopped", "Stopped"))
        self._append_output(self._lang.get("install_manual_stop", "[Stopped]"))

    def _run_install(self):
        script = os.path.join(SCRIPT_DIR, "install.sh")
        if not os.path.exists(script):
            self.after(0, lambda: self._append_output(f"[Error] Script not found: {script}"))
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
            self.after(0, lambda: self._append_output(f"[Exception] {e}"))
        finally:
            self._install_running = False
            self.after(0, lambda: self._install_btn.configure(state="normal"))
            self.after(0, lambda: self._stop_btn.configure(state="disabled"))

    def _handle_install_line(self, line):
        self._append_output(line)
        # Parse progress
        m = re.match(r"PROGRESS:(\d+)/(\d+):(.+)", line)
        if m:
            step, total, msg = int(m.group(1)), int(m.group(2)), m.group(3)
            pct = (step / total) * 100
            self._progress_var.set(pct)
            self._progress_label.configure(text=f"{step}/{total}: {msg}")
        elif line.startswith("NETWORK_REGION:"):
            region = line.split(":")[1]
            region_text = self._lang.get("network_cn", "CN Network") if region == "cn" else self._lang.get("network_global", "Global Network")
            self._net_label.configure(text=region_text,
                                      fg=COLORS["warning"] if region == "cn" else COLORS["success"])

    # ===== Status Monitor =====
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
                getattr(self, attr).configure(text=self._lang.get("status_detect_failed", "Failed"), fg=COLORS["error"])
            return
        installed = data.get("installed", False)
        status    = data.get("status", "unknown")
        version   = data.get("version", "unknown")
        pid       = data.get("pid", "—")
        config    = data.get("config", "—") or "—"

        self._st_installed.configure(
            text=self._lang.get("status_installed", "Installed") + (" ✓" if installed else ""),
            fg=COLORS["success"] if installed else COLORS["error"])
        self._st_status.configure(
            text=self._lang.get("status_running", "Running") if status == "running" else self._lang.get("status_stopped", "Stopped"),
            fg=COLORS["success"] if status == "running" else COLORS["subtext"])
        self._st_version.configure(text=version, fg=COLORS["text"])
        self._st_pid.configure(text=pid or "—", fg=COLORS["text"])
        self._st_config.configure(text=config, fg=COLORS["text"])

    def _run_cmd(self, cmd):
        def do_run():
            try:
                subprocess.run(cmd, check=True)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=do_run, daemon=True).start()

    # ===== Settings Save =====
    def _save_settings(self):
        registry = self._settings_vars["npm_registry"].get()
        try:
            subprocess.run(["npm", "config", "set", "registry", registry], check=True)
            messagebox.showinfo(self._lang.get("save_success", "Success"),
                              f"{self._lang.get('npm_mirror_set', 'npm registry set to:')}\n{registry}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ===== Integration Save =====
    def _save_integration(self, platform):
        fields = self._integration_entries.get(platform, {})
        args = [fields[k].get().strip() for k in fields]

        if not all(args):
            messagebox.showwarning("Warning", self._lang.get("fill_all_fields", "Please fill all fields"))
            return

        script = os.path.join(SCRIPT_DIR, "integrations.sh")
        cmd = ["bash", script, platform] + args

        def do_save():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self.after(0, lambda: messagebox.showinfo(self._lang.get("save_success", "Success"),
                                                             self._lang.get("config_saved", "Config saved")))
                else:
                    err = result.stderr or result.stdout
                    self.after(0, lambda: messagebox.showerror("Error", err))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=do_save, daemon=True).start()

    # ===== Load Logs =====
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
                self._log_text.insert("1.0", f"Failed to read log: {e}")
        else:
            self._log_text.insert("1.0", self._lang.get("no_logs", "No logs"))
        self._log_text.configure(state="disabled")

    def destroy(self):
        if self._status_timer:
            self.after_cancel(self._status_timer)
        super().destroy()


if __name__ == "__main__":
    app = OpenClawInstaller()
    app.mainloop()
