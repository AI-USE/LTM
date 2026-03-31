import customtkinter as ctk
import tkinter as tk
import time
import random
import logging
from ui_theme import CyberTheme, MatrixRain
from config_manager import ConfigManager

logger = logging.getLogger("SHINOBI.UI")

# 外観モードの設定
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class ShinobiLockScreen:
    """
    CustomTkinterを用いた、洗練された「シノビ」極致ロック画面。
    墨色、朱色、金色を基調とした重厚なデザイン。
    """
    def __init__(self, root, on_auth_success=None):
        self.root = root
        self.root.title("SHINOBI - ACCESS RESTRICTED")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="#000000")
        self.root.wm_attributes("-topmost", True)
        self.on_auth_success = on_auth_success

        # 背景のマトリックス・レイン (Canvas)
        self.matrix_canvas = MatrixRain(self.root)
        self.matrix_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # メインコンテナ (中央配置)
        self.main_frame = ctk.CTkFrame(
            self.root,
            width=500,
            height=600,
            fg_color="#0D0D0D",
            border_width=2,
            border_color="#FF003C", # 朱色
            corner_radius=20
        )
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.create_widgets()
        self.animate_boot()

    def create_widgets(self):
        # センターロゴ
        self.logo_label = ctk.CTkLabel(
            self.main_frame,
            text="忍 SHINOBI 忍",
            font=("Consolas", 48, "bold"),
            text_color="#FF003C"
        )
        self.logo_label.pack(pady=(50, 10))

        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text=">>> UNAUTHORIZED ACCESS DETECTED <<<",
            font=("Consolas", 14),
            text_color="#FF003C"
        )
        self.status_label.pack(pady=5)

        # リアルタイムログ
        self.log_label = ctk.CTkLabel(
            self.main_frame,
            text="BOOTING SECURE MODULES...",
            font=("Consolas", 12),
            text_color="#00FF41",
            justify="left",
            width=400,
            anchor="w"
        )
        self.log_label.pack(pady=20, padx=40)

        # プログレスバー
        self.pbar = ctk.CTkProgressBar(self.main_frame, width=400, height=10, progress_color="#FF003C", fg_color="#1a1a1a")
        self.pbar.set(0)
        self.pbar.pack(pady=10)

        # PIN入力
        self.pin_entry = ctk.CTkEntry(
            self.main_frame,
            placeholder_text="Enter Master PIN",
            show="*",
            width=300,
            height=50,
            font=("Consolas", 24),
            fg_color="#1a1a1a",
            border_color="#FF003C",
            text_color="#00FF41",
            justify="center"
        )
        self.pin_entry.pack(pady=30)
        self.pin_entry.bind("<Return>", self.on_pin_submit)

        # 解錠ボタン
        self.unlock_btn = ctk.CTkButton(
            self.main_frame,
            text="EXECUTE UNLOCK",
            command=self.on_pin_submit,
            width=300,
            height=50,
            font=("Consolas", 16, "bold"),
            fg_color="#FF003C",
            hover_color="#CC0030",
            text_color="black"
        )
        self.unlock_btn.pack(pady=20)

    def animate_boot(self):
        messages = [
            "SHINOBI_CORE: LOADING...",
            "DECRYPTING MFA_SYSTEM...",
            "SCANNING BIOMETRICS...",
            "BITLOCKER PROTECTION: VERIFIED",
            "STANDBY: WAITING FOR MASTER"
        ]
        def step(idx):
            if idx < len(messages):
                self.log_label.configure(text=f"> {messages[idx]}")
                self.pbar.set((idx + 1) / len(messages))
                self.root.after(200, lambda: step(idx + 1))
            else:
                self.status_label.configure(text=">>> STATUS: READY - AUTHORIZATION REQUIRED <<<", text_color="#00E5FF")
        step(0)

    def on_pin_submit(self, event=None):
        pin = self.pin_entry.get()
        if ConfigManager.verify_pin(pin):
            self.handle_success()
        else:
            self.handle_failure()

    def handle_success(self):
        self.log_label.configure(text="> ACCESS GRANTED. WELCOME MASTER.", text_color="#00FF41")
        self.status_label.configure(text=">>> [ DECRYPTING SESSION ] <<<", text_color="#00FF41")
        self.pbar.configure(progress_color="#00FF41")

        if self.on_auth_success:
            self.on_auth_success("PIN")

        def fade(alpha):
            if alpha > 0:
                self.root.attributes("-alpha", alpha)
                self.root.after(30, lambda: fade(alpha - 0.1))
            else:
                self.root.destroy()
        self.root.after(800, lambda: fade(1.0))

    def handle_failure(self):
        self.pin_entry.delete(0, tk.END)
        self.log_label.configure(text="> ACCESS DENIED: INVALID TOKEN", text_color="#FF003C")
        def flash(count):
            if count > 0:
                color = "#FF003C" if count % 2 == 0 else "#0D0D0D"
                self.main_frame.configure(border_color=color)
                self.root.after(100, lambda: flash(count - 1))
            else:
                self.main_frame.configure(border_color="#FF003C")
        flash(6)

class AdminDashboard(ctk.CTk):
    """
    管理者用プロフェッショナル・ダッシュボード。
    """
    def __init__(self):
        super().__init__()
        self.title("SHINOBI - ADMIN INTERFACE v3.0")
        self.geometry("1100x700")
        self.configure(fg_color="#0D0D0D")
        ConfigManager.initialize()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#1a1a1a")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="SHINOBI", font=ctk.CTkFont(size=24, weight="bold"), text_color="#FF003C")
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.nav_monitor_btn = ctk.CTkButton(self.sidebar_frame, text=" MONITORING ", command=lambda: self.select_tab("monitor"), fg_color="transparent", text_color="#00FF41", hover_color="#333")
        self.nav_monitor_btn.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        self.nav_settings_btn = ctk.CTkButton(self.sidebar_frame, text=" CONFIGURATION ", command=lambda: self.select_tab("config"), fg_color="transparent", text_color="#00FF41", hover_color="#333")
        self.nav_settings_btn.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        self.nav_logs_btn = ctk.CTkButton(self.sidebar_frame, text=" AUDIT_LOGS ", command=lambda: self.select_tab("logs"), fg_color="transparent", text_color="#00FF41", hover_color="#333")
        self.nav_logs_btn.grid(row=3, column=0, sticky="ew", padx=10, pady=5)

        self.main_content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(0, weight=1)

        self.tabs = {}
        self.build_monitor_tab()
        self.build_config_tab()
        self.build_logs_tab()

        self.select_tab("monitor")
        self.update_clock()

    def select_tab(self, name):
        for tab_name, tab_frame in self.tabs.items():
            tab_frame.grid_forget()
        self.tabs[name].grid(row=0, column=0, sticky="nsew")

    def build_monitor_tab(self):
        tab = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.tabs["monitor"] = tab
        ctk.CTkLabel(tab, text="[ REALTIME_SYSTEM_MONITOR ]", font=ctk.CTkFont(size=20, weight="bold"), text_color="#00E5FF").pack(pady=(0, 20), anchor="w")
        status_frame = ctk.CTkFrame(tab, fg_color="#1a1a1a", border_width=1, border_color="#333")
        status_frame.pack(fill="x", pady=10)
        self.clock_label = ctk.CTkLabel(status_frame, text="TIME: 00:00:00", font=("Consolas", 18), text_color="#00FF41")
        self.clock_label.pack(side="left", padx=20, pady=15)
        self.sys_status = ctk.CTkLabel(status_frame, text="STATUS: STABLE_OPS", font=("Consolas", 18), text_color="#00FF41")
        self.sys_status.pack(side="right", padx=20, pady=15)

    def build_config_tab(self):
        tab = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.tabs["config"] = tab
        ctk.CTkLabel(tab, text="[ CONFIGURATION_NODE ]", font=ctk.CTkFont(size=20, weight="bold"), text_color="#00E5FF").pack(pady=(0, 20), anchor="w")
        self.rssi_slider = self.create_slider_item(tab, "RSSI_THRESHOLD_DBM", -90, -30, ConfigManager.get("rssi_threshold"))
        self.face_slider = self.create_slider_item(tab, "FACE_PRECISION_DELTA", 0.3, 0.7, ConfigManager.get("face_threshold"))
        ctk.CTkButton(tab, text=">>> DEPLOY_CONFIG <<<", command=self.save_settings, height=50, fg_color="#FF003C", hover_color="#CC0030", text_color="black", font=("Consolas", 16, "bold")).pack(pady=40, fill="x")

    def create_slider_item(self, parent, label, from_, to_, value):
        frame = ctk.CTkFrame(parent, fg_color="#1a1a1a", border_width=1, border_color="#333")
        frame.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(frame, text=label, font=("Consolas", 12), text_color="#00FF41").pack(side="left", padx=20, pady=20)
        slider = ctk.CTkSlider(frame, from_=from_, to=to_, progress_color="#00FF41", button_color="#00FF41")
        slider.set(value)
        slider.pack(side="right", expand=True, padx=20)
        return slider

    def build_logs_tab(self):
        tab = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.tabs["logs"] = tab
        ctk.CTkLabel(tab, text="[ SYSTEM_AUDIT_LOG_STREAM ]", font=ctk.CTkFont(size=20, weight="bold"), text_color="#00E5FF").pack(pady=(0, 20), anchor="w")
        self.log_textbox = ctk.CTkTextbox(tab, fg_color="#050505", text_color="#00FF41", font=("Consolas", 12), border_width=1, border_color="#333")
        self.log_textbox.pack(expand=True, fill="both", pady=10)

    def update_clock(self):
        self.clock_label.configure(text=f"TIME: {time.strftime('%H:%M:%S')}")
        self.after(1000, self.update_clock)

    def save_settings(self):
        ConfigManager.set("rssi_threshold", int(self.rssi_slider.get()))
        ConfigManager.set("face_threshold", round(float(self.face_slider.get()), 2))
        messagebox.showinfo("SHINOBI_ADMIN", "CONFIGURATION DEPLOYED SUCCESSFULLY.")
