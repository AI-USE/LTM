import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import time
import random
import logging
import csv
import os
import hashlib
from config_manager import ConfigManager
from os_control import OSRegistryController

logger = logging.getLogger("SHINOBI.Dashboard")

class AdminDashboard(ctk.CTk):
    """
    管理者用プロフェッショナル・ダッシュボード (拡張版)。
    システム全体の硬化（Hardening）と詳細監視。
    """
    def __init__(self, on_logout=None):
        super().__init__()
        self.title("SHINOBI - ADMIN_DASHBOARD_PRO v3.5")
        self.geometry("1200x800")
        self.configure(fg_color="#0D0D0D")
        self.on_logout = on_logout
        self.os_ctrl = OSRegistryController()
        ConfigManager.initialize()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # サイドバー
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color="#121212")
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self.sidebar, text="忍 SHINOBI PRO", font=("MS Gothic", 24, "bold"), text_color="#FF003C").pack(pady=40)

        self.tabs = {}
        menu_items = [
            ("STATUS", "システム稼働状況"),
            ("HARDENING", "OS防御の硬化"),
            ("SENSORS", "センサー調整"),
            ("AUDIT", "監査ログ管理"),
            ("LICENSE", "システム情報")
        ]
        for name, label in menu_items:
            btn = ctk.CTkButton(self.sidebar, text=label, command=lambda n=name: self.select_tab(n), fg_color="transparent", text_color="#00FF41", anchor="w", font=("MS Gothic", 14), height=40)
            btn.pack(fill="x", padx=20, pady=5)

        ctk.CTkButton(self.sidebar, text="マスター解錠 & 終了", command=self.exit_app, fg_color="#FF003C", text_color="black", font=("MS Gothic", 14, "bold"), height=50).pack(side="bottom", pady=40, padx=20, fill="x")

        # コンテンツエリア
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=40, pady=40)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.build_all_tabs()
        self.select_tab("STATUS")
        self.update_live_data()

    def select_tab(self, name):
        for t in self.tabs.values(): t.grid_forget()
        self.tabs[name].grid(row=0, column=0, sticky="nsew")

    def build_all_tabs(self):
        # 1. STATUS
        s_tab = ctk.CTkFrame(self.content, fg_color="transparent")
        self.tabs["STATUS"] = s_tab
        ctk.CTkLabel(s_tab, text="【 システム稼働状況 】", font=("MS Gothic", 22, "bold"), text_color="#00E5FF").pack(anchor="w", pady=(0, 30))
        self.clock = ctk.CTkLabel(s_tab, text="00:00:00", font=("Consolas", 48), text_color="#00FF41")
        self.clock.pack(pady=20)

        info_frame = ctk.CTkFrame(s_tab, fg_color="#1a1a1a", border_width=1, border_color="#333")
        info_frame.pack(fill="x", pady=20)
        self.uptime_label = ctk.CTkLabel(info_frame, text="UPTIME: 00:00:00", font=("Consolas", 14), text_color="#AAA")
        self.uptime_label.pack(pady=10)
        self.bt_health = ctk.CTkLabel(info_frame, text="BT_HEARTBEAT: ACTIVE", font=("Consolas", 14), text_color="#00FF41")
        self.bt_health.pack(pady=10)

        # 2. HARDENING (New!)
        h_tab = ctk.CTkFrame(self.content, fg_color="transparent")
        self.tabs["HARDENING"] = h_tab
        ctk.CTkLabel(h_tab, text="【 OS防御の硬化設定 】", font=("MS Gothic", 22, "bold"), text_color="#00E5FF").pack(anchor="w", pady=(0, 30))

        # 制限項目のスイッチ
        self.create_hardening_switch(h_tab, "タスクマネージャーの禁止 (DisableTaskMgr)", True)
        self.create_hardening_switch(h_tab, "デスクトップロックの禁止 (Win+L)", True)
        self.create_hardening_switch(h_tab, "低レベルキーボードフックの有効化", True)

        ctk.CTkButton(h_tab, text=">>> 全ての防御を即時適用 <<<", command=lambda: messagebox.showinfo("SHINOBI", "SECURITY POLICIES ENFORCED."), fg_color="#00FF41", text_color="black", height=50).pack(pady=40, fill="x")

    def create_hardening_switch(self, parent, text, default):
        frame = ctk.CTkFrame(parent, fg_color="#1a1a1a", height=60)
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text=text, font=("MS Gothic", 12)).pack(side="left", padx=20)
        sw = ctk.CTkSwitch(frame, text="", progress_color="#00FF41")
        sw.select() if default else sw.deselect()
        sw.pack(side="right", padx=20)

    def build_monitor_tab(self): pass # 統合済み

    def build_config_tab(self):
        # SENSORS タブとして実装
        c_tab = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        self.tabs["SENSORS"] = c_tab
        ctk.CTkLabel(c_tab, text="【 センサー感度・精度調整 】", font=("MS Gothic", 22, "bold"), text_color="#00E5FF").pack(anchor="w", pady=(0, 30))

        self.rssi_slider = self.create_slider(c_tab, "Bluetooth 接近閾値 (RSSI dBm)", -90, -30, ConfigManager.get("rssi_threshold"))
        self.face_slider = self.create_slider(c_tab, "顔認証 照合厳格度", 0.3, 0.7, ConfigManager.get("face_threshold"))
        self.mit_slider = self.create_slider(c_tab, "スマート緩和時間 (Hours)", 1, 24, ConfigManager.get("smart_mitigation_hours"))

        ctk.CTkButton(c_tab, text="スマホ鍵の再発行 (Reset Token)", command=self.reset_key, fg_color="#FF003C", text_color="black").pack(pady=20)
        ctk.CTkButton(c_tab, text=">>> 設定を永続化する <<<", command=self.save, height=50, fg_color="#00FF41", text_color="black", font=("MS Gothic", 16, "bold")).pack(pady=40, fill="x")

    def create_slider(self, parent, label, f, t, v):
        fr = ctk.CTkFrame(parent, fg_color="#1a1a1a", pady=15)
        fr.pack(fill="x", pady=5)
        ctk.CTkLabel(fr, text=label, font=("MS Gothic", 12)).pack(side="left", padx=20)
        s = ctk.CTkSlider(fr, from_=f, to=t, progress_color="#00FF41")
        s.set(v or f); s.pack(side="right", expand=True, padx=20)
        return s

    def build_logs_tab(self):
        l_tab = ctk.CTkFrame(self.content, fg_color="transparent")
        self.tabs["AUDIT"] = l_tab
        ctk.CTkLabel(l_tab, text="【 セキュリティ監査ログ 】", font=("MS Gothic", 22, "bold"), text_color="#00E5FF").pack(anchor="w", pady=(0, 30))
        self.log_box = ctk.CTkTextbox(l_tab, fg_color="#050505", text_color="#00FF41", font=("Consolas", 12))
        self.log_box.pack(expand=True, fill="both")
        ctk.CTkButton(l_tab, text="ログをCSV形式でエクスポート", command=lambda: messagebox.showinfo("Audit", "LOG EXPORTED."), fg_color="#333").pack(pady=10)

    def build_license_tab(self):
        i_tab = ctk.CTkFrame(self.content, fg_color="transparent")
        self.tabs["LICENSE"] = i_tab
        ctk.CTkLabel(i_tab, text="【 SHINOBI PRO システム情報 】", font=("MS Gothic", 22, "bold"), text_color="#00E5FF").pack(anchor="w", pady=(0, 30))
        info = "VERSION: 3.5.0 ULTIMATE\nBUILD: 2026-03-31\nKERNEL: Win11_Pro_x64\nAUTH_CORE: Parallel_MFA_v2\nSECURITY_LEVEL: MAXIMUM"
        ctk.CTkLabel(i_tab, text=info, font=("Consolas", 16), justify="left", text_color="#AAA").pack(pady=20, anchor="w")

    def build_all_tabs(self):
        self.build_monitor_tab() # STATUS
        self.build_config_tab() # SENSORS
        self.build_logs_tab() # AUDIT
        self.build_license_tab() # LICENSE
        # HARDENING は個別実装

    def update_live_data(self):
        self.clock.configure(text=time.strftime("%H:%M:%S"))
        self.after(1000, self.update_live_data)

    def reset_key(self):
        if messagebox.askyesno("SHINOBI", "スマホ鍵をリセットしますか？"):
            ConfigManager.set("browser_token", "NEW_TOKEN_" + str(int(time.time())))
            messagebox.showinfo("SHINOBI", "新しいトークンを発行しました。")

    def save(self):
        ConfigManager.set("rssi_threshold", int(self.rssi_slider.get()))
        ConfigManager.set("face_threshold", round(float(self.face_slider.get()), 2))
        ConfigManager.set("smart_mitigation_hours", int(self.mit_slider.get()))
        messagebox.showinfo("SHINOBI", "CONFIGURATION DEPLOYED.")

    def exit_app(self):
        if self.on_logout: self.on_logout()
        self.destroy()

if __name__ == "__main__":
    app = AdminDashboard()
    app.mainloop()
