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
from os_control import OSRegistryController, is_admin

logger = logging.getLogger("SHINOBI.Dashboard")

class AdminDashboard(ctk.CTk):
    """
    管理者用プロフェッショナル・ダッシュボード v4.0。
    二段階認証を伴う保護ロジックを統合。
    """
    def __init__(self, on_logout=None):
        super().__init__()
        self.title("SHINOBI - ADMIN_DASHBOARD_PRO v4.0")
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
        for name, label in [("STATUS", "状況監視"), ("HARDENING", "OS硬化"), ("SENSORS", "感度調整"), ("AUDIT", "監査ログ"), ("SYSTEM", "高度な設定")]:
            btn = ctk.CTkButton(self.sidebar, text=label, command=lambda n=name: self.select_tab(n), fg_color="transparent", text_color="#00FF41", anchor="w", font=("MS Gothic", 14), height=45)
            btn.pack(fill="x", padx=20, pady=5)

        ctk.CTkButton(self.sidebar, text="安全に終了してロック", command=self.exit_app, fg_color="#FF003C", text_color="black", font=("MS Gothic", 14, "bold"), height=55).pack(side="bottom", pady=40, padx=20, fill="x")

        # コンテンツ
        self.container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew", padx=40, pady=40)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.build_all_tabs()
        self.select_tab("STATUS")
        self.update_clock()

    def select_tab(self, name):
        for t in self.tabs.values(): t.grid_forget()
        self.tabs[name].grid(row=0, column=0, sticky="nsew")

    def build_all_tabs(self):
        # STATUS
        t_status = ctk.CTkFrame(self.container, fg_color="transparent")
        self.tabs["STATUS"] = t_status
        ctk.CTkLabel(t_status, text="【 システム稼働状況 】", font=("MS Gothic", 22, "bold"), text_color="#00E5FF").pack(anchor="w", pady=(0, 20))
        self.clock_label = ctk.CTkLabel(t_status, text="00:00:00", font=("Consolas", 42), text_color="#00FF41")
        self.clock_label.pack(pady=30)

        # HARDENING
        t_hard = ctk.CTkFrame(self.container, fg_color="transparent")
        self.tabs["HARDENING"] = t_hard
        ctk.CTkLabel(t_hard, text="【 OS防御の硬化設定 】", font=("MS Gothic", 22, "bold"), text_color="#00E5FF").pack(anchor="w", pady=(0, 20))
        self.create_sw(t_hard, "タスクマネージャーの禁止", True)
        self.create_sw(t_hard, "低レベルキーボードフックの常時有効化", True)
        self.create_sw(t_hard, "Win+L ロックの無効化", True)

        # SENSORS
        t_sensor = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        self.tabs["SENSORS"] = t_sensor
        ctk.CTkLabel(t_sensor, text="【 センサー調整 】", font=("MS Gothic", 22, "bold"), text_color="#00E5FF").pack(anchor="w", pady=(0, 20))
        self.rssi_sl = self.create_sl(t_sensor, "Bluetooth RSSI 閾値 (-90 to -30)", -90, -30, ConfigManager.get("rssi_threshold"))
        self.face_sl = self.create_sl(t_sensor, "顔認証 精度閾値 (0.3 to 0.7)", 0.3, 0.7, ConfigManager.get("face_threshold"))
        ctk.CTkButton(t_sensor, text=">>> 設定を保存して適用 <<<", command=self.save_cfg, fg_color="#00FF41", text_color="black", height=50).pack(pady=40, fill="x")

        # AUDIT
        t_audit = ctk.CTkFrame(self.container, fg_color="transparent")
        self.tabs["AUDIT"] = t_audit
        ctk.CTkLabel(t_audit, text="【 監査ログ管理 】", font=("MS Gothic", 22, "bold"), text_color="#00E5FF").pack(anchor="w", pady=(0, 20))
        self.log_text = ctk.CTkTextbox(t_audit, fg_color="#050505", text_color="#00FF41", font=("Consolas", 12))
        self.log_text.pack(expand=True, fill="both", pady=10)

        # SYSTEM (高度な保護)
        t_sys = ctk.CTkFrame(self.container, fg_color="transparent")
        self.tabs["SYSTEM"] = t_sys
        ctk.CTkLabel(t_sys, text="【 高度な保護と初期化 】", font=("MS Gothic", 22, "bold"), text_color="#FF003C").pack(anchor="w", pady=(0, 20))

        info_f = ctk.CTkFrame(t_sys, fg_color="#1a1a1a", border_width=1, border_color="#FF003C")
        info_f.pack(fill="x", pady=20)
        ctk.CTkLabel(info_f, text="システムの初期化・アンインストールにはマスターPINによる二段階認証が必要です。", font=("MS Gothic", 12), text_color="#AAA", pady=20).pack()

        ctk.CTkButton(t_sys, text="システムリセット (1日待機ルール)", command=self.request_reset, fg_color="#333").pack(pady=10, fill="x")
        ctk.CTkButton(t_sys, text="SHINOBIをアンインストールする", command=self.request_uninstall, fg_color="#FF003C", text_color="black").pack(pady=10, fill="x")

    def create_sw(self, p, t, v):
        f = ctk.CTkFrame(p, fg_color="#1a1a1a", height=60)
        f.pack(fill="x", pady=5)
        ctk.CTkLabel(f, text=t, font=("MS Gothic", 12)).pack(side="left", padx=20)
        sw = ctk.CTkSwitch(f, text="", progress_color="#00FF41")
        sw.select() if v else sw.deselect(); sw.pack(side="right", padx=20)

    def create_sl(self, p, t, f, to, v):
        fr = ctk.CTkFrame(p, fg_color="#1a1a1a", pady=15)
        fr.pack(fill="x", pady=5)
        ctk.CTkLabel(fr, text=t, font=("MS Gothic", 12)).pack(side="left", padx=20)
        s = ctk.CTkSlider(fr, from_=f, to=to, progress_color="#00FF41")
        s.set(v or f); s.pack(side="right", expand=True, padx=20)
        return s

    def update_clock(self):
        self.clock_label.configure(text=time.strftime("%H:%M:%S"))
        self.after(1000, self.update_clock)

    def save_cfg(self):
        ConfigManager.set("rssi_threshold", int(self.rssi_sl.get()))
        ConfigManager.set("face_threshold", round(float(self.face_sl.get()), 2))
        messagebox.showinfo("SHINOBI", "CONFIGURATION DEPLOYED.")

    def request_reset(self):
        if messagebox.askyesno("CONFIRM", "システムリセットを申請しますか？\nセキュリティ保護のため、実行は24時間後となります。"):
            ConfigManager.set("reset_request_time", time.time())
            messagebox.showinfo("SHINOBI", "リセット申請を受理しました。24時間後に再度実行してください。")

    def request_uninstall(self):
        # 簡易二段階認証（本来は別要素）
        from tkinter import simpledialog
        p = simpledialog.askstring("認証", "アンインストールを許可するにはマスターPINを入力してください:", show='*')
        if p and ConfigManager.verify_pin(p):
            if messagebox.askyesno("最終確認", "本当にアンインストールしますか？\nレジストリ制限を全て解除し、標準のシェルを復元します。"):
                self.os_ctrl.restore_explorer_shell()
                self.os_ctrl.set_lock_mode(False)
                messagebox.showinfo("SHINOBI", "防衛機能を解除しました。手動でファイルを削除してください。")
                self.destroy()

    def exit_app(self):
        if self.on_logout: self.on_logout()
        self.destroy()

if __name__ == "__main__":
    app = AdminDashboard()
    app.mainloop()
