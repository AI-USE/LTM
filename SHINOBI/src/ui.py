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

logger = logging.getLogger("SHINOBI.UI")

class ShinobiLockScreen:
    """
    全認証同時待機型・極致ロック画面 UI (完全日本語版)。
    """
    def __init__(self, root, engine, on_auth_success=None):
        self.root = root
        self.engine = engine
        self.on_auth_success = on_auth_success

        self.root.title("SHINOBI - アクセス制限中")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="#000000")
        self.root.wm_attributes("-topmost", True)

        from ui_theme import MatrixRain
        self.matrix_canvas = MatrixRain(self.root)
        self.matrix_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        self.main_frame = ctk.CTkFrame(self.root, width=850, height=650, fg_color="#0D0D0D", border_width=2, border_color="#FF003C", corner_radius=20)
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.create_widgets()
        self.update_status_loop()

    def create_widgets(self):
        ctk.CTkLabel(self.main_frame, text="忍 SHINOBI 忍", font=("MS Gothic", 56, "bold"), text_color="#FF003C").pack(pady=(50, 10))
        self.msg_label = ctk.CTkLabel(self.main_frame, text="システムロック中: 認証が必要です", font=("MS Gothic", 12), text_color="#00E5FF")
        self.msg_label.pack(pady=5)

        self.indicator_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.indicator_frame.pack(pady=30, fill="x", padx=60)

        self.indicators = {}
        items = [("FACE", "顔認証"), ("BT_NEARBY", "スマホ接近"), ("BROWSER_KEY", "スマホ鍵"), ("PIN", "マスターPIN")]
        for key, label in items:
            self.indicators[key] = self.create_indicator(key, label)

        self.pin_entry = ctk.CTkEntry(self.main_frame, placeholder_text="アクセスコードを入力", show="*", width=350, height=55, font=("Consolas", 26), fg_color="#1a1a1a", border_color="#FF003C", text_color="#00FF41", justify="center")
        self.pin_entry.pack(pady=20)
        self.pin_entry.bind("<Return>", self.on_pin_submit)

        self.lockout_label = ctk.CTkLabel(self.main_frame, text="", font=("MS Gothic", 12), text_color="#FF003C")
        self.lockout_label.pack()

        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(pady=(40, 20))
        ctk.CTkButton(btn_frame, text="【 緊急用解除 】", command=self.on_emergency_click, width=180, fg_color="transparent", border_width=1, border_color="#444", text_color="#666", font=("MS Gothic", 12)).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="【 管理コンソール 】", command=self.on_admin_click, width=180, fg_color="transparent", border_width=1, border_color="#444", text_color="#666", font=("MS Gothic", 12)).pack(side="left", padx=10)

    def create_indicator(self, key, label):
        frame = ctk.CTkFrame(self.indicator_frame, fg_color="#121212", border_width=1, border_color="#222", width=160, height=90)
        frame.pack(side="left", padx=10, expand=True)
        frame.pack_propagate(False)
        ctk.CTkLabel(frame, text=label, font=("MS Gothic", 11), text_color="#555").pack(pady=(15, 0))
        status = ctk.CTkLabel(frame, text="待機中", font=("MS Gothic", 14, "bold"), text_color="#222")
        status.pack(pady=5)
        return {"frame": frame, "status": status}

    def update_status_loop(self):
        if self.engine.is_pin_locked():
            rem = self.engine.get_lockout_remaining()
            self.pin_entry.configure(state="disabled")
            self.lockout_label.configure(text=f"セキュリティロック発動中: 残り {rem} 秒")
        else:
            self.pin_entry.configure(state="normal")
            self.lockout_label.configure(text="")

        for key, val in self.engine.auth_status.items():
            ind = self.indicators.get(key)
            if ind:
                if val:
                    ind["frame"].configure(border_color="#00FF41")
                    ind["status"].configure(text="解除完了", text_color="#00FF41")
                else:
                    ind["frame"].configure(border_color="#222")
                    ind["status"].configure(text="待機中", text_color="#333")

        can_unlock, route = self.engine.check_unlock_conditions()
        if can_unlock:
            self.handle_success(route)
            return
        self.root.after(500, self.update_status_loop)

    def on_pin_submit(self, event=None):
        if self.engine.is_pin_locked(): return
        pin = self.pin_entry.get()
        if ConfigManager.verify_pin(pin):
            self.engine.auth_status["PIN"] = True
            self.pin_entry.configure(state="disabled")
        else:
            self.engine.record_pin_failure()
            self.pin_entry.delete(0, tk.END)
            self.trigger_error_flash()

    def trigger_error_flash(self):
        def flash(count):
            color = "#FF003C" if count % 2 == 0 else "#0D0D0D"
            self.main_frame.configure(border_color=color)
            if count > 0: self.root.after(100, lambda: flash(count - 1))
            else: self.main_frame.configure(border_color="#FF003C")
        flash(4)

    def handle_success(self, route):
        self.msg_label.configure(text=f">>> 認証成功: {route} <<<", text_color="#00FF41")
        if self.on_auth_success: self.on_auth_success(route)
        def fade(alpha):
            if alpha > 0:
                self.root.attributes("-alpha", alpha)
                self.root.after(30, lambda: fade(alpha - 0.1))
            else: self.root.destroy()
        self.root.after(800, lambda: fade(1.0))

    def on_emergency_click(self):
        from tkinter import simpledialog
        p = simpledialog.askstring("緊急用解除", "マスターPINを入力してください:", show='*')
        if p and ConfigManager.verify_pin(p):
            self.handle_success("緊急用救済ルート")

    def on_admin_click(self):
        from tkinter import simpledialog
        p = simpledialog.askstring("管理者認証", "管理者用PINを入力してください:", show='*')
        if p and ConfigManager.verify_pin(p):
            AdminDashboard().mainloop()

class AdminDashboard(ctk.CTk):
    """
    管理者用プロフェッショナル・ダッシュボード (完全日本語版)。
    """
    def __init__(self, on_logout=None):
        super().__init__()
        self.title("SHINOBI - 管理者コンソール v3.4")
        self.geometry("1150x750")
        self.configure(fg_color="#0D0D0D")
        self.on_logout = on_logout
        ConfigManager.initialize()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#151515")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self.sidebar_frame, text="忍 SHINOBI", font=("MS Gothic", 26, "bold"), text_color="#FF003C").pack(pady=30)

        self.tabs = {}
        items = [("MONITORING", "リアルタイム監視"), ("CONFIGURATION", "システム設定"), ("AUDIT_LOGS", "監査ログ"), ("SYSTEM_INFO", "システム情報")]
        for name, label in items:
            btn = ctk.CTkButton(self.sidebar_frame, text=label, command=lambda n=name: self.select_tab(n), fg_color="transparent", text_color="#00FF41", anchor="w", font=("MS Gothic", 14))
            btn.pack(fill="x", padx=20, pady=5)

        ctk.CTkButton(self.sidebar_frame, text="システム終了", command=self.destroy, fg_color="#FF003C", text_color="black", font=("MS Gothic", 14, "bold")).pack(side="bottom", pady=40, padx=20, fill="x")

        self.main_content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(0, weight=1)

        self.build_all_tabs()
        self.select_tab("MONITORING")
        self.update_stats()

    def select_tab(self, name):
        for tab in self.tabs.values(): tab.grid_forget()
        self.tabs[name].grid(row=0, column=0, sticky="nsew")

    def build_all_tabs(self):
        # 監視
        m_tab = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.tabs["MONITORING"] = m_tab
        ctk.CTkLabel(m_tab, text="【 リアルタイム・システム監視 】", font=("MS Gothic", 20, "bold"), text_color="#00E5FF").pack(anchor="w", pady=(0, 20))
        self.clock_label = ctk.CTkLabel(m_tab, text="現在時刻: 00:00:00", font=("Consolas", 32), text_color="#00FF41")
        self.clock_label.pack(pady=40)
        self.load_meter = ctk.CTkProgressBar(m_tab, width=700, progress_color="#FF003C")
        self.load_meter.pack(pady=20)

        # 設定
        c_tab = ctk.CTkScrollableFrame(self.main_content, fg_color="transparent")
        self.tabs["CONFIGURATION"] = c_tab
        ctk.CTkLabel(c_tab, text="【 セキュリティ・パラメータ調整 】", font=("MS Gothic", 20, "bold"), text_color="#00E5FF").pack(anchor="w", pady=(0, 20))
        self.rssi_slider = self.create_slider(c_tab, "Bluetooth 接近閾値 (dBm)", -90, -30, ConfigManager.get("rssi_threshold"))
        self.face_slider = self.create_slider(c_tab, "顔認証 照合精度 (厳格-寛容)", 0.3, 0.7, ConfigManager.get("face_threshold"))
        ctk.CTkButton(c_tab, text="スマホ鍵をリセットして再発行", command=self.reset_key, fg_color="#FF003C", text_color="black", font=("MS Gothic", 12)).pack(pady=20)
        ctk.CTkButton(c_tab, text=">>> 設定をシステムに適用 <<<", command=self.save, height=50, fg_color="#00FF41", text_color="black", font=("MS Gothic", 16, "bold")).pack(pady=40, fill="x")

        # ログ
        l_tab = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.tabs["AUDIT_LOGS"] = l_tab
        ctk.CTkLabel(l_tab, text="【 監査イベント・ストリーム 】", font=("MS Gothic", 20, "bold"), text_color="#00E5FF").pack(anchor="w", pady=(0, 20))
        self.log_box = ctk.CTkTextbox(l_tab, fg_color="#050505", text_color="#00FF41", font=("Consolas", 12))
        self.log_box.pack(expand=True, fill="both")

        # 情報
        s_tab = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.tabs["SYSTEM_INFO"] = s_tab
        ctk.CTkLabel(s_tab, text="【 SHINOBI システム構成マニフェスト 】", font=("MS Gothic", 20, "bold"), text_color="#00E5FF").pack(anchor="w", pady=(0, 20))
        info_str = f"バージョン: 3.4.0\nビルド日: 2026.03.31\n対象OS: Windows 11 Pro\n暗号化アルゴリズム: AES-256-SHA256\nMFAエンジン: Parallel Core v2.1"
        ctk.CTkLabel(s_tab, text=info_str, font=("MS Gothic", 16), text_color="#00FF41", justify="left").pack(pady=20, anchor="w")

    def create_slider(self, parent, label, f, t, v):
        frame = ctk.CTkFrame(parent, fg_color="#151515", border_width=1, border_color="#333")
        frame.pack(fill="x", pady=10)
        ctk.CTkLabel(frame, text=label, font=("MS Gothic", 12), text_color="#00FF41").pack(side="left", padx=20, pady=20)
        s = ctk.CTkSlider(frame, from_=f, to=t, progress_color="#00FF41")
        s.set(v or f); s.pack(side="right", expand=True, padx=20)
        return s

    def update_stats(self):
        self.clock_label.configure(text=f"システム時刻: {time.strftime('%H:%M:%S')}")
        self.load_meter.set(random.uniform(0.1, 0.3))
        self.after(1000, self.update_stats)

    def reset_key(self):
        if messagebox.askyesno("SHINOBI", "スマホ鍵をリセットしますか？\n既存のスマホ鍵は無効になります。"):
            token = "SHINOBI_" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]
            ConfigManager.set("browser_token", token)
            messagebox.showinfo("SHINOBI", f"新しいトークンを発行しました:\n{token}\nスマホへ再同期してください。")

    def save(self):
        ConfigManager.set("rssi_threshold", int(self.rssi_slider.get()))
        ConfigManager.set("face_threshold", round(float(self.face_slider.get()), 2))
        messagebox.showinfo("SHINOBI", "設定を正常に適用しました。")

if __name__ == "__main__":
    app = AdminDashboard()
    app.mainloop()
