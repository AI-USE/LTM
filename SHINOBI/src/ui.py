import tkinter as tk
from tkinter import ttk, messagebox
import random
import time
import logging
from config_manager import ConfigManager
from ui_theme import CyberTheme, MatrixRain

logger = logging.getLogger("SHINOBI.UI")

class ShinobiLockScreen:
    """
    究極の「ハッカー風」全画面ロック画面 UI (UX強化版)。
    """
    def __init__(self, root, on_auth_success=None):
        self.root = root
        self.root.title("SHINOBI - ACCESS RESTRICTED")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg=CyberTheme.BG_COLOR)
        self.root.wm_attributes("-topmost", True)
        self.on_auth_success = on_auth_success

        # 背景のマトリックス・レイン
        self.matrix_canvas = MatrixRain(self.root)
        self.matrix_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # UIレイヤー
        self.ui_frame = tk.Frame(self.root, bg=CyberTheme.BG_COLOR, highlightthickness=2, highlightbackground=CyberTheme.FG_ACCENT)
        self.ui_frame.place(relx=0.5, rely=0.5, anchor="center", width=600, height=500)

        self.create_widgets()
        self.start_boot_sequence()

    def create_widgets(self):
        self.title_label = tk.Label(
            self.ui_frame, text="[ SHINOBI ]", font=CyberTheme.FONT_HEADER,
            fg=CyberTheme.FG_ACCENT, bg=CyberTheme.BG_COLOR
        )
        self.title_label.pack(pady=(40, 10))

        self.alert_label = tk.Label(
            self.ui_frame, text=">>> UNAUTHORIZED ACCESS DETECTED <<<",
            font=("Consolas", 12), fg=CyberTheme.FG_WARNING, bg=CyberTheme.BG_COLOR
        )
        self.alert_label.pack(pady=10)

        self.log_text = tk.Label(
            self.ui_frame, text="INITIALIZING SYSTEM...",
            font=("Consolas", 10), fg=CyberTheme.FG_ACCENT, bg=CyberTheme.BG_COLOR,
            justify=tk.LEFT, width=50, anchor="w"
        )
        self.log_text.pack(pady=20, padx=20)

        self.scan_bar = ttk.Progressbar(self.ui_frame, orient="horizontal", length=400, mode="determinate")
        self.scan_bar.pack(pady=10)

        self.pin_frame = tk.Frame(self.ui_frame, bg=CyberTheme.BG_COLOR)
        self.pin_frame.pack(pady=30)

        tk.Label(self.pin_frame, text="ID/PIN:", font=CyberTheme.FONT_MONO, fg=CyberTheme.FG_ACCENT, bg=CyberTheme.BG_COLOR).pack(side=tk.LEFT, padx=10)
        self.pin_entry = tk.Entry(self.pin_frame, show="*", font=("Consolas", 24), width=10, bg="#222", fg=CyberTheme.FG_ACCENT, insertbackground=CyberTheme.FG_ACCENT, relief=tk.FLAT)
        self.pin_entry.pack(side=tk.LEFT)
        self.pin_entry.bind("<Return>", self.on_pin_submit)

        self.unlock_btn = tk.Button(
            self.ui_frame, text="EXECUTE UNLOCK", command=self.on_pin_submit,
            font=CyberTheme.FONT_MONO, bg="#1a1a1a", fg=CyberTheme.FG_ACCENT, width=20, relief=tk.GROOVE, activebackground=CyberTheme.FG_ACCENT, activeforeground="black"
        )
        self.unlock_btn.pack(pady=20)

    def start_boot_sequence(self):
        messages = [
            "KERNEL BOOTING...",
            "DECRYPTING MFA MODULE...",
            "SCANNING PERIPHERAL DEVICES...",
            "ESTABLISHING BLUETOOTH HANDSHAKE...",
            "ACTIVATING BIOMETRIC SCANNER...",
            "SYSTEM READY. WAITING FOR AUTHENTICATION."
        ]

        def update_log(idx):
            if idx < len(messages):
                self.log_text.config(text=f"> {messages[idx]}")
                self.scan_bar["value"] = (idx + 1) * (100 / len(messages))
                self.root.after(200, lambda: update_log(idx + 1))
            else:
                self.alert_label.config(text=">>> STATUS: STANDBY - WAITING FOR MASTER <<<", fg=CyberTheme.FG_INFO)

        update_log(0)

    def on_pin_submit(self, event=None):
        pin = self.pin_entry.get()
        if ConfigManager.verify_pin(pin):
            self.show_unlock_animation()
            if self.on_auth_success:
                self.on_auth_success("PIN")
        else:
            self.trigger_alert()

    def trigger_alert(self):
        self.pin_entry.delete(0, tk.END)
        self.log_text.config(text="> ACCESS DENIED: INVALID SECURITY TOKEN", fg=CyberTheme.FG_WARNING)

        def flash(count):
            if count > 0:
                color = CyberTheme.FG_WARNING if count % 2 == 0 else CyberTheme.BG_COLOR
                self.ui_frame.config(highlightbackground=color)
                self.root.after(100, lambda: flash(count - 1))
            else:
                self.ui_frame.config(highlightbackground=CyberTheme.FG_ACCENT)

        flash(6)
        logger.warning("Authentication failure detected.")

    def show_unlock_animation(self):
        self.log_text.config(text="> KEY VERIFIED. DECRYPTING USER SESSION...", fg=CyberTheme.FG_ACCENT)
        self.title_label.config(fg=CyberTheme.FG_INFO, text="[ ACCESS GRANTED ]")
        self.scan_bar["value"] = 100

        def fade_out(opacity):
            if opacity > 0:
                self.root.attributes("-alpha", opacity)
                self.root.after(30, lambda: fade_out(opacity - 0.1))
            else:
                self.root.destroy()

        self.root.after(500, lambda: fade_out(1.0))

class AdminDashboard:
    """
    管理者用「サイバー風」デジタルメーター・ダッシュボード。
    """
    def __init__(self, root):
        self.root = root
        self.root.title("SHINOBI - ADMIN_DASHBOARD_v2.1")
        self.root.geometry("1000x750")
        self.root.configure(bg=CyberTheme.BG_COLOR)
        ConfigManager.initialize()

        self.create_widgets()
        self.update_stats()

    def create_widgets(self):
        header_frame = tk.Frame(self.root, bg=CyberTheme.BG_COLOR)
        header_frame.pack(fill="x", pady=20)

        tk.Label(header_frame, text="[ SHINOBI ADMIN INTERFACE ]", font=("Consolas", 24, "bold"), fg=CyberTheme.FG_INFO, bg=CyberTheme.BG_COLOR).pack()
        self.time_label = tk.Label(header_frame, text="SYSTEM_TIME: 00:00:00", font=CyberTheme.FONT_MONO, fg=CyberTheme.FG_ACCENT, bg=CyberTheme.BG_COLOR)
        self.time_label.pack()

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Cyber.TNotebook", background=CyberTheme.BG_COLOR, borderwidth=1, bordercolor=CyberTheme.FG_ACCENT)
        style.configure("Cyber.TNotebook.Tab", background="#1a1a1a", foreground=CyberTheme.FG_ACCENT, font=CyberTheme.FONT_MONO, padding=[20, 5])
        style.map("Cyber.TNotebook.Tab", background=[("selected", CyberTheme.FG_ACCENT)], foreground=[("selected", "black")])
        style.configure("Cyber.TFrame", background=CyberTheme.BG_COLOR)

        tab_control = ttk.Notebook(self.root, style="Cyber.TNotebook")

        sensor_tab = ttk.Frame(tab_control, style="Cyber.TFrame")
        tab_control.add(sensor_tab, text=" [ MONITORING_SENSORS ] ")
        self.build_sensor_tab(sensor_tab)

        log_tab = ttk.Frame(tab_control, style="Cyber.TFrame")
        tab_control.add(log_tab, text=" [ AUDIT_LOGS_DB ] ")
        self.build_log_tab(log_tab)

        tab_control.pack(expand=1, fill="both", padx=30, pady=10)

    def build_sensor_tab(self, parent):
        container = tk.Frame(parent, bg=CyberTheme.BG_COLOR)
        container.pack(expand=True, fill="both")

        rssi_frame = tk.LabelFrame(container, text=" BLE_RSSI_PROXIMITY_DETECTION ", font=CyberTheme.FONT_MONO, fg=CyberTheme.FG_ACCENT, bg=CyberTheme.BG_COLOR, padx=20, pady=20, highlightthickness=1)
        rssi_frame.pack(pady=20, fill="x", padx=40)

        self.rssi_slider = tk.Scale(rssi_frame, from_=-90, to=-30, orient="horizontal", bg=CyberTheme.BG_COLOR, fg=CyberTheme.FG_ACCENT, highlightthickness=0, font=("Consolas", 14), length=700, troughcolor="#111", activebackground=CyberTheme.FG_INFO)
        self.rssi_slider.set(ConfigManager.get("rssi_threshold"))
        self.rssi_slider.pack(pady=10)

        face_frame = tk.LabelFrame(container, text=" FACE_RECOGNITION_PRECISION_ENGINE ", font=CyberTheme.FONT_MONO, fg=CyberTheme.FG_ACCENT, bg=CyberTheme.BG_COLOR, padx=20, pady=20, highlightthickness=1)
        face_frame.pack(pady=20, fill="x", padx=40)

        self.face_slider = tk.Scale(face_frame, from_=0.3, to_=0.7, resolution=0.01, orient="horizontal", bg=CyberTheme.BG_COLOR, fg=CyberTheme.FG_ACCENT, highlightthickness=0, font=("Consolas", 14), length=700, troughcolor="#111", activebackground=CyberTheme.FG_INFO)
        self.face_slider.set(ConfigManager.get("face_threshold"))
        self.face_slider.pack(pady=10)

        btn_frame = tk.Frame(container, bg=CyberTheme.BG_COLOR)
        btn_frame.pack(pady=40)

        save_btn = tk.Button(btn_frame, text=">>> COMPILE & SAVE CONFIGURATION <<<", command=self.save_settings, font=("Consolas", 14, "bold"), bg="#1a1a1a", fg=CyberTheme.FG_ACCENT, width=40, height=2, relief=tk.RAISED, activebackground=CyberTheme.FG_ACCENT, activeforeground="black")
        save_btn.pack()

    def build_log_tab(self, parent):
        self.log_list = tk.Listbox(parent, font=("Consolas", 11), bg="#050505", fg=CyberTheme.FG_ACCENT, highlightcolor=CyberTheme.FG_ACCENT, selectbackground=CyberTheme.FG_INFO, selectforeground="black", borderwidth=1, relief=tk.FLAT)
        self.log_list.pack(expand=1, fill="both", padx=20, pady=20)

    def update_stats(self):
        current_time = time.strftime("%H:%M:%S")
        self.time_label.config(text=f"SYSTEM_TIME: {current_time} [STABLE]")
        self.root.after(1000, self.update_stats)

    def save_settings(self):
        ConfigManager.set("rssi_threshold", int(self.rssi_slider.get()))
        ConfigManager.set("face_threshold", round(float(self.face_slider.get()), 2))
        messagebox.showinfo("SYSTEM_ADMIN", "CONFIGURATION COMPILED SUCCESSFULLY.")
        logger.info("Admin updated sensors.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AdminDashboard(root)
    root.mainloop()
