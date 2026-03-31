import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import logging
from config_manager import ConfigManager

logger = logging.getLogger("SHINOBI.UI")

class ShinobiLockScreen:
    """
    SHINOBIの全画面ロック画面 UI (日本語版)。
    """
    def __init__(self, root, on_auth_success=None):
        self.root = root
        self.root.title("SHINOBI - アクセス拒否")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="black")
        self.root.wm_attributes("-topmost", True)
        self.on_auth_success = on_auth_success

        self.create_widgets()

    def create_widgets(self):
        # メインタイトル
        self.title_label = tk.Label(
            self.root, text="SHINOBI", font=("Consolas", 72, "bold"),
            fg="#FF0000", bg="black"
        )
        self.title_label.pack(pady=(100, 20))

        # ステータス
        self.status_label = tk.Label(
            self.root, text="認証デバイスをスキャン中...",
            font=("MS Gothic", 18), fg="#00FF00", bg="black"
        )
        self.status_label.pack(pady=20)

        # PIN入力フォーム
        self.pin_frame = tk.Frame(self.root, bg="black")
        self.pin_frame.pack(pady=40)

        tk.Label(self.pin_frame, text="PINを入力:", font=("MS Gothic", 14), fg="white", bg="black").pack(side=tk.LEFT, padx=10)
        self.pin_entry = tk.Entry(self.pin_frame, show="*", font=("Consolas", 24), width=10, bg="#222", fg="white", insertbackground="white")
        self.pin_entry.pack(side=tk.LEFT)
        self.pin_entry.bind("<Return>", self.on_pin_submit)

        # ロック解除ボタン
        self.unlock_btn = tk.Button(
            self.root, text="解錠", command=self.on_pin_submit,
            font=("MS Gothic", 18), bg="#333", fg="white", width=15, relief=tk.FLAT
        )
        self.unlock_btn.pack(pady=20)

    def on_pin_submit(self, event=None):
        pin = self.pin_entry.get()
        if ConfigManager.verify_pin(pin):
            self.show_unlock_animation()
            if self.on_auth_success:
                self.on_auth_success("PIN")
        else:
            self.pin_entry.delete(0, tk.END)
            self.status_label.config(text="アクセス拒否: PINが正しくありません", fg="red")
            logger.warning("不正確なPIN入力試行。")

    def show_unlock_animation(self):
        self.status_label.config(text="認証成功。おかえりなさい。", fg="#00FF00")
        self.root.after(1000, self.root.destroy)

class AdminDashboard:
    """
    管理者用設定画面 UI (日本語版)。
    """
    def __init__(self, root):
        self.root = root
        self.root.title("SHINOBI 管理者ダッシュボード")
        self.root.geometry("800x600")
        ConfigManager.initialize()
        self.create_widgets()

    def create_widgets(self):
        tab_control = ttk.Notebook(self.root)

        # タブ1: センサー調整
        sensor_tab = ttk.Frame(tab_control)
        tab_control.add(sensor_tab, text="センサー設定")
        self.build_sensor_tab(sensor_tab)

        # タブ2: 監査ログ
        log_tab = ttk.Frame(tab_control)
        tab_control.add(log_tab, text="監査ログ")
        self.build_log_tab(log_tab)

        tab_control.pack(expand=1, fill="both")

    def build_sensor_tab(self, parent):
        # Bluetooth RSSI 調整
        ttk.Label(parent, text="Bluetooth接近閾値 (dBm):", font=("MS Gothic", 12)).pack(pady=(20, 5))
        self.rssi_slider = ttk.Scale(parent, from_=-90, to=-30, orient="horizontal")
        self.rssi_slider.set(ConfigManager.get("rssi_threshold"))
        self.rssi_slider.pack(pady=10, fill="x", padx=40)

        # 顔認証精度調整
        ttk.Label(parent, text="顔認証精度 (厳格 0.3 - 0.7 寛容):", font=("MS Gothic", 12)).pack(pady=(20, 5))
        self.face_slider = ttk.Scale(parent, from_=0.3, to_=0.7, orient="horizontal")
        self.face_slider.set(ConfigManager.get("face_threshold"))
        self.face_slider.pack(pady=10, fill="x", padx=40)

        # 保存ボタン
        ttk.Button(parent, text="設定を適用", command=self.save_settings).pack(pady=40)

    def build_log_tab(self, parent):
        self.log_list = tk.Listbox(parent, font=("Consolas", 10), bg="#f0f0f0")
        self.log_list.pack(expand=1, fill="both", padx=10, pady=10)

    def save_settings(self):
        ConfigManager.set("rssi_threshold", int(self.rssi_slider.get()))
        ConfigManager.set("face_threshold", round(float(self.face_slider.get()), 2))
        messagebox.showinfo("SHINOBI", "設定を保存しました。")
        logger.info("管理者ダッシュボードから設定を更新。")

if __name__ == "__main__":
    root = tk.Tk()
    app = AdminDashboard(root)
    root.mainloop()
