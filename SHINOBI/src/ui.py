import customtkinter as ctk
import tkinter as tk
import time
import random
import logging
import threading
from ui_theme import CyberTheme, MatrixRain
from config_manager import ConfigManager

logger = logging.getLogger("SHINOBI.UI")

class ShinobiLockScreen:
    """
    全認証同時待機型・極致ロック画面。
    """
    def __init__(self, root, engine, on_auth_success=None):
        self.root = root
        self.engine = engine
        self.root.title("SHINOBI - ACCESS RESTRICTED")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="#000000")
        self.root.wm_attributes("-topmost", True)
        self.on_auth_success = on_auth_success

        # 背景のマトリックス・レイン
        self.matrix_canvas = MatrixRain(self.root)
        self.matrix_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # メインフレーム
        self.main_frame = ctk.CTkFrame(self.root, width=800, height=650, fg_color="#0D0D0D", border_width=2, border_color="#FF003C", corner_radius=20)
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.create_widgets()
        self.update_status_loop()

    def create_widgets(self):
        # センターロゴ
        ctk.CTkLabel(self.main_frame, text="忍 SHINOBI 忍", font=("Consolas", 48, "bold"), text_color="#FF003C").pack(pady=(40, 10))

        # 認証インジケーター・エリア
        self.indicator_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.indicator_frame.pack(pady=20, fill="x", padx=100)

        self.indicators = {}
        self.create_indicator("FACE", "顔認証")
        self.create_indicator("BT_NEARBY", "スマホ接近")
        self.create_indicator("BROWSER_KEY", "スマホ鍵")
        self.create_indicator("PIN", "PIN認証")

        # 警告 / メッセージ
        self.msg_label = ctk.CTkLabel(self.main_frame, text="2要素の認証をクリアしてください", font=("MS Gothic", 12), text_color="#00E5FF")
        self.msg_label.pack(pady=5)

        # PIN入力
        self.pin_entry = ctk.CTkEntry(self.main_frame, placeholder_text="ENTER PIN", show="*", width=300, height=50, font=("Consolas", 24), fg_color="#1a1a1a", border_color="#FF003C", text_color="#00FF41", justify="center")
        self.pin_entry.pack(pady=20)
        self.pin_entry.bind("<Return>", self.on_pin_submit)

        # ロックアウト・タイマー
        self.lockout_label = ctk.CTkLabel(self.main_frame, text="", font=("Consolas", 12), text_color="#FF003C")
        self.lockout_label.pack()

        # 緊急用解錠ボタン（救済ルート）
        self.emergency_btn = ctk.CTkButton(self.main_frame, text="[ EMERGENCY_BYPASS ]", command=self.on_emergency_click, width=200, height=30, fg_color="transparent", border_width=1, border_color="#666", text_color="#666", font=("Consolas", 10))
        self.emergency_btn.pack(pady=(40, 10))

    def create_indicator(self, key, label):
        frame = ctk.CTkFrame(self.indicator_frame, fg_color="#1a1a1a", border_width=1, border_color="#333", width=140, height=80)
        frame.pack(side="left", padx=10, expand=True)
        frame.pack_propagate(False)

        title = ctk.CTkLabel(frame, text=label, font=("MS Gothic", 10), text_color="#666")
        title.pack(pady=(10, 0))

        status = ctk.CTkLabel(frame, text="WAITING", font=("Consolas", 14, "bold"), text_color="#333")
        status.pack(pady=5)

        self.indicators[key] = {"frame": frame, "status": status, "title": title}

    def update_status_loop(self):
        """認証状態をリアルタイム監視。"""
        # PINロックアウトの確認
        if self.engine.is_pin_locked():
            rem = self.engine.get_lockout_remaining()
            self.pin_entry.configure(state="disabled")
            self.lockout_label.configure(text=f"SECURITY LOCKOUT: {rem}s")
        else:
            self.pin_entry.configure(state="normal")
            self.lockout_label.configure(text="")

        # 各インジケーターの更新
        for key, val in self.engine.auth_status.items():
            ind = self.indicators.get(key)
            if ind:
                if val:
                    ind["frame"].configure(border_color="#00FF41")
                    ind["status"].configure(text="CLEAR", text_color="#00FF41")
                    ind["title"].configure(text_color="#00FF41")
                else:
                    ind["frame"].configure(border_color="#333")
                    ind["status"].configure(text="WAITING", text_color="#333")
                    ind["title"].configure(text_color="#666")

        # 解錠判定
        can_unlock, route = self.engine.check_unlock_conditions()
        if can_unlock:
            self.handle_success(route)
            return # ループ終了

        self.root.after(500, self.update_status_loop)

    def on_pin_submit(self, event=None):
        if self.engine.is_pin_locked(): return

        pin = self.pin_entry.get()
        if ConfigManager.verify_pin(pin):
            self.engine.auth_status["PIN"] = True
            self.pin_entry.delete(0, tk.END)
            self.pin_entry.configure(state="disabled")
            logger.info("PIN Verified.")
        else:
            penalty = self.engine.record_pin_failure()
            self.pin_entry.delete(0, tk.END)
            if penalty > 0:
                logger.warning(f"Lockout triggered: {penalty}s")
            else:
                self.trigger_error_flash()

    def trigger_error_flash(self):
        def flash(count):
            if count > 0:
                color = "#FF003C" if count % 2 == 0 else "#0D0D0D"
                self.main_frame.configure(border_color=color)
                self.root.after(100, lambda: flash(count - 1))
            else: self.main_frame.configure(border_color="#FF003C")
        flash(4)

    def handle_success(self, route):
        self.msg_label.configure(text=f">>> {route.upper()} VERIFIED <<<", text_color="#00FF41")
        if self.on_auth_success: self.on_auth_success(route)

        def fade(alpha):
            if alpha > 0:
                self.root.attributes("-alpha", alpha)
                self.root.after(30, lambda: fade(alpha - 0.1))
            else: self.root.destroy()
        self.root.after(1000, lambda: fade(1.0))

    def on_emergency_click(self):
        # 救済ルート（別途起動）
        from tkinter import simpledialog
        p = simpledialog.askstring("EMERGENCY", "Enter Master PIN for Recovery:", show='*')
        if p and ConfigManager.verify_pin(p):
            # 顔写真を強制撮影して解錠
            self.handle_success("Emergency Recovery")

if __name__ == "__main__":
    from mfa_engine import MFAEngine
    root = ctk.CTk()
    engine = MFAEngine()
    # テスト用に1要素クリア
    # engine.auth_status["FACE"] = True
    app = ShinobiLockScreen(root, engine)
    root.mainloop()
