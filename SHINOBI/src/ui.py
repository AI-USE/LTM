import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import time
import random
import logging
import cv2
import face_recognition
try:
    from ui_theme import CyberTheme, MatrixRain
    from config_manager import ConfigManager
    from face_auth import FaceAuth
except ImportError:
    from .ui_theme import CyberTheme, MatrixRain
    from .config_manager import ConfigManager
    from .face_auth import FaceAuth

logger = logging.getLogger("SHINOBI.UI")

class ShinobiLockScreen:
    """
    全認証同時待機型・極致ロック画面 UI (v4.2)。
    救済ルート（RESCUE_EVIDENCE）の実装。
    """
    def __init__(self, root, engine, on_auth_success=None):
        self.root = root
        self.engine = engine
        self.on_auth_success = on_auth_success
        self.face_auth = FaceAuth()

        self.root.title("SHINOBI - ACCESS RESTRICTED")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="#000000")
        self.root.wm_attributes("-topmost", True)

        from ui_theme import MatrixRain
        self.matrix_canvas = MatrixRain(self.root)
        self.matrix_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        self.main_frame = ctk.CTkFrame(self.root, width=850, height=650, fg_color="#0D0D0D", border_width=2, border_color="#FF003C", corner_radius=20)
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.create_widgets()
        self.update_loop()

    def create_widgets(self):
        ctk.CTkLabel(self.main_frame, text="忍 SHINOBI 忍", font=("MS Gothic", 56, "bold"), text_color="#FF003C").pack(pady=(50, 10))
        self.st_msg = ctk.CTkLabel(self.main_frame, text=">>> システム防衛オンライン <<<", font=("MS Gothic", 12), text_color="#00E5FF")
        self.st_msg.pack(pady=5)

        self.ind_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.ind_frame.pack(pady=30, fill="x", padx=60)

        self.indicators = {}
        for k, l in [("FACE", "顔認証"), ("BT_NEARBY", "スマホ接近"), ("BROWSER_KEY", "スマホ鍵"), ("PIN", "暗証番号")]:
            self.indicators[k] = self.create_indicator(l)

        self.pin_entry = ctk.CTkEntry(self.main_frame, placeholder_text="暗証番号（PIN）を入力", show="*", width=350, height=55, font=("Consolas", 26), fg_color="#1a1a1a", border_color="#FF003C", text_color="#00FF41", justify="center")
        self.pin_entry.pack(pady=20)
        self.pin_entry.bind("<Return>", self.on_pin_submit)

        self.lock_label = ctk.CTkLabel(self.main_frame, text="", font=("MS Gothic", 12), text_color="#FF003C")
        self.lock_label.pack()

        btn_f = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_f.pack(pady=(40, 20))
        ctk.CTkButton(btn_f, text="【 救済ルート実行 】", command=self.on_rescue, width=180, fg_color="transparent", border_width=1, border_color="#444", text_color="#666", font=("MS Gothic", 12)).pack(side="left", padx=10)

    def create_indicator(self, label):
        f = ctk.CTkFrame(self.ind_frame, fg_color="#121212", border_width=1, border_color="#222", width=160, height=90)
        f.pack(side="left", padx=10, expand=True)
        f.pack_propagate(False)
        ctk.CTkLabel(f, text=label, font=("MS Gothic", 11), text_color="#555").pack(pady=(15, 0))
        status = ctk.CTkLabel(f, text="待機中", font=("MS Gothic", 14, "bold"), text_color="#222")
        status.pack(pady=5)
        return {"frame": f, "status": status}

    def update_loop(self):
        if self.engine.is_pin_locked():
            self.pin_entry.configure(state="disabled")
            self.lock_label.configure(text=f"セキュリティロック中: 残り {self.engine.get_lockout_remaining()} 秒")
        else:
            self.pin_entry.configure(state="normal")
            self.lock_label.configure(text="")

        for k, v in self.engine.auth_status.items():
            ind = self.indicators.get(k)
            if ind:
                if v:
                    ind["frame"].configure(border_color="#00FF41")
                    ind["status"].configure(text="解除完了", text_color="#00FF41")
                else:
                    ind["frame"].configure(border_color="#222")
                    ind["status"].configure(text="待機中", text_color="#333")

        ok, route = self.engine.check_unlock_conditions()
        if ok:
            self.handle_success(route)
            return
        self.root.after(500, self.update_loop)

    def on_pin_submit(self, e=None):
        if self.engine.is_pin_locked(): return
        if ConfigManager.verify_pin(self.pin_entry.get()):
            self.engine.auth_status["PIN"] = True
            self.pin_entry.configure(state="disabled")
            logger.info("PIN認証に成功しました。")
        else:
            self.engine.record_pin_failure()
            self.pin_entry.delete(0, tk.END)
            self.flash_error()

    def flash_error(self):
        def f(c):
            col = "#FF003C" if c % 2 == 0 else "#0D0D0D"
            self.main_frame.configure(border_color=col)
            if c > 0: self.root.after(100, lambda: f(c - 1))
            else: self.main_frame.configure(border_color="#FF003C")
        f(4)

    def handle_success(self, route):
        self.st_msg.configure(text=f">>> 認証成功: {route.upper()} <<<", text_color="#00FF41")
        if self.on_auth_success: self.on_auth_success(route)
        def fade(a):
            if a > 0:
                self.root.attributes("-alpha", a)
                self.root.after(30, lambda: fade(a - 0.1))
            else: self.root.destroy()
        self.root.after(1000, lambda: fade(1.0))

    def on_rescue(self):
        """救済ルート: PIN + 強制顔スキャン (証拠記録)。"""
        from tkinter import simpledialog
        p = simpledialog.askstring("救済認証", "マスターPINを入力してください:", show='*')
        if not p or not ConfigManager.verify_pin(p):
            messagebox.showerror("拒否", "PINが一致しません。")
            return

        messagebox.showinfo("SHINOBI", "PINを照合しました。次に、解錠の証拠として顔スキャンを強制実行します。\nカメラを直視してください。")

        # 実際に顔が映っているかチェック
        success = False
        for i in range(5): # 5回試行
            frame = self.face_auth.capture_safe()
            if frame is not None:
                # 顔の存在を確認 (hogモデル)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                locs = face_recognition.face_locations(rgb, model="hog")
                if locs:
                    # 証拠として保存
                    from audit_watchdog import AuditLog
                    AuditLog().log_entry("RESCUE_EVIDENCE", face_img_frame=frame, status="RESCUE_UNLOCK")
                    success = True
                    break
            time.sleep(1)

        if success:
            messagebox.showinfo("認証成功", "証拠写真を記録しました。システムを解錠します。")
            self.handle_success("救済ルート(証拠記録済み)")
        else:
            messagebox.showerror("認証失敗", "顔を検知できませんでした。スキャナを遮らないでください。")
