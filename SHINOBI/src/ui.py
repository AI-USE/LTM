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
    管理者用プロフェッショナル・ダッシュボード v4.1。
    リアルタイム・センサーフィードバック機能搭載。
    """
    def __init__(self, app_context=None, on_logout=None):
        super().__init__()
        self.app = app_context # ShinobiApp への参照
        self.title("SHINOBI - ADMIN_DASHBOARD_PRO v4.1")
        self.geometry("1200x850")
        self.configure(fg_color="#0D0D0D")
        self.on_logout = on_logout
        self.os_ctrl = OSRegistryController()
        ConfigManager.initialize()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # サイドバー
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color="#121212")
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self.sidebar, text="忍 SHINOBI PRO", font=("MS Gothic", 26, "bold"), text_color="#FF003C").pack(pady=40)

        self.tabs = {}
        items = [("STATUS", "状況監視"), ("HARDENING", "OS硬化"), ("SENSORS", "感度調整"), ("AUDIT", "監査ログ")]
        for name, label in items:
            btn = ctk.CTkButton(self.sidebar, text=label, command=lambda n=name: self.select_tab(n), fg_color="transparent", text_color="#00FF41", anchor="w", font=("MS Gothic", 14), height=45)
            btn.pack(fill="x", padx=20, pady=5)

        ctk.CTkButton(self.sidebar, text="マスター解錠 & 終了", command=self.exit_app, fg_color="#FF003C", text_color="black", font=("MS Gothic", 14, "bold"), height=55).pack(side="bottom", pady=40, padx=20, fill="x")

        # コンテンツ
        self.container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew", padx=40, pady=40)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.build_all_tabs()
        self.select_tab("STATUS")
        self.update_live_ui()

    def select_tab(self, name):
        for t in self.tabs.values(): t.grid_forget()
        self.tabs[name].grid(row=0, column=0, sticky="nsew")

    def build_all_tabs(self):
        # STATUS (リアルタイムフィードバック)
        t_status = ctk.CTkFrame(self.container, fg_color="transparent")
        self.tabs["STATUS"] = t_status
        ctk.CTkLabel(t_status, text="【 リアルタイム・センサー監視 】", font=("MS Gothic", 22, "bold"), text_color="#00E5FF").pack(anchor="w", pady=(0, 20))

        self.clock = ctk.CTkLabel(t_status, text="00:00:00", font=("Consolas", 42), text_color="#00FF41")
        self.clock.pack(pady=20)

        # センサーメーター
        meter_frame = ctk.CTkFrame(t_status, fg_color="#121212", border_width=1, border_color="#333", padx=20, pady=20)
        meter_frame.pack(fill="x", pady=20)

        # BT RSSI
        ctk.CTkLabel(meter_frame, text="BLUETOOTH SIGNAL (RSSI)", font=("Consolas", 12), text_color="#00E5FF").pack(anchor="w")
        self.bt_val_lbl = ctk.CTkLabel(meter_frame, text="-120 dBm", font=("Consolas", 24, "bold"), text_color="#00FF41")
        self.bt_val_lbl.pack(pady=5)
        self.bt_pbar = ctk.CTkProgressBar(meter_frame, progress_color="#00FF41")
        self.bt_pbar.set(0); self.bt_pbar.pack(fill="x", pady=(0, 20))

        # Face Distance
        ctk.CTkLabel(meter_frame, text="BIOMETRIC DISTANCE (PRECISION)", font=("Consolas", 12), text_color="#00E5FF").pack(anchor="w")
        self.face_val_lbl = ctk.CTkLabel(meter_frame, text="1.0000", font=("Consolas", 24, "bold"), text_color="#00FF41")
        self.face_val_lbl.pack(pady=5)
        self.face_pbar = ctk.CTkProgressBar(meter_frame, progress_color="#FF003C")
        self.face_pbar.set(0); self.face_pbar.pack(fill="x")

        # HARDENING / SENSORS / AUDIT ... (他は既存通り)
        self.tabs["HARDENING"] = ctk.CTkFrame(self.container, fg_color="transparent")
        self.tabs["SENSORS"] = ctk.CTkFrame(self.container, fg_color="transparent")
        self.tabs["AUDIT"] = ctk.CTkFrame(self.container, fg_color="transparent")

    def update_live_ui(self):
        """リアルタイムでセンサーの生データを表示。"""
        self.clock.configure(text=time.strftime("%H:%M:%S"))

        # アプリコンテキストから値を取得
        if self.app:
            # BT RSSI
            rssi = self.app.bt.current_rssi
            self.bt_val_lbl.configure(text=f"{rssi} dBm")
            # -120 to -30 の範囲を 0.0 to 1.0 にマップ
            bt_p = max(0, min(1, (rssi + 120) / 90))
            self.bt_pbar.set(bt_p)

            # Face (最新の照合結果)
            dist = getattr(self.app, 'last_face_dist', 1.0)
            self.face_val_lbl.configure(text=f"{dist:.4f}")
            # 1.0 to 0.0 の範囲を 0.0 to 1.0 にマップ (近いほど高い)
            face_p = 1.0 - dist
            self.face_pbar.set(face_p)

        self.after(1000, self.update_live_ui)

    def exit_app(self):
        if self.on_logout: self.on_logout()
        self.destroy()
