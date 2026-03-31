import customtkinter as ctk
from tkinter import messagebox
import hashlib
import time
import os
import qrcode
from PIL import Image, ImageTk
import logging
import asyncio
import threading
import json
from config_manager import ConfigManager
from face_auth import FaceAuth
from os_control import OSRegistryController, is_admin
from bt_monitor import BluetoothMonitor

logger = logging.getLogger("SHINOBI.Wizard")

class SetupWizard(ctk.CTkToplevel):
    """
    SHINOBI QRペアリング対応セットアップ・ウィザード。
    """
    def __init__(self, parent, on_complete=None):
        super().__init__(parent)
        self.title("SHINOBI - ULTIMATE SETUP WIZARD v3.3")
        self.geometry("800x650")
        self.configure(fg_color="#0D0D0D")
        self.attributes("-topmost", True)
        self.on_complete = on_complete

        self.face = FaceAuth()
        self.os_ctrl = OSRegistryController()

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(expand=True, fill="both", padx=60, pady=40)

        self.show_step_1()

    def show_step_1(self):
        """ステップ1: マスターPINの設定"""
        self.clear_container()
        self.create_header("STEP 1: MASTER PIN", "システム解錠に使用する4桁以上の数字を設定してください。")
        self.pin_entry = ctk.CTkEntry(self.container, placeholder_text="New PIN", show="*", width=300, height=45, font=("Consolas", 20), justify="center")
        self.pin_entry.pack(pady=20)
        self.create_next_button(self.process_step_1)

    def process_step_1(self):
        pin = self.pin_entry.get()
        if len(pin) < 4:
            messagebox.showwarning("SHINOBI", "PINは4桁以上で設定してください。")
            return
        ConfigManager.set("pin_hash", hashlib.sha256(pin.encode()).hexdigest())
        self.show_step_2()

    def show_step_2(self):
        """ステップ2: 顔データの登録"""
        self.clear_container()
        self.create_header("STEP 2: BIOMETRIC SCAN", "カメラを直視してください。特徴量をスキャンします。")
        self.scan_label = ctk.CTkLabel(self.container, text="STATUS: READY", font=("Consolas", 14), text_color="#00FF41")
        self.scan_label.pack(pady=30)
        ctk.CTkButton(self.container, text="START FACE SCAN", command=self.process_step_2, fg_color="#FF003C", text_color="black", font=("Consolas", 14, "bold")).pack(pady=20)

    def process_step_2(self):
        self.scan_label.configure(text="SCANNING... DO NOT MOVE")
        self.update()
        if self.face.register_face("master"):
            messagebox.showinfo("SHINOBI", "顔認証のセットアップが完了しました。")
            self.show_step_3()
        else:
            messagebox.showerror("SHINOBI", "スキャン失敗。")

    def show_step_3(self):
        """ステップ3: Bluetoothスマホペアリング (QRコード)"""
        self.clear_container()
        self.create_header("STEP 3: MOBILE KEY PAIRING", "スマホのブラウザでこのQRコードを読み取り、ペアリングを完了してください。")

        # トークンの生成
        token = "SHINOBI_" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]
        ConfigManager.set("browser_token", token)

        # QRコード用データの作成 (JSON形式)
        # 実際にはスマホ用サイトのURLにパラメータとして付与
        qr_data = {
            "u": "12345678-1234-5678-1234-567812345678", # Service UUID
            "c": "87654321-4321-8765-4321-876543210987", # Characteristic UUID
            "t": token # Initial Token
        }
        qr_str = json.dumps(qr_data)

        # QRコード生成
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_str)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # Tkinter用に変換
        img = img.resize((250, 250))
        self.qr_photo = ImageTk.PhotoImage(img)

        qr_label = tk.Label(self.container, image=self.qr_photo, bg="white")
        qr_label.pack(pady=10)

        ctk.CTkLabel(self.container, text=f"SECRET_TOKEN: {token}", font=("Consolas", 10), text_color="#00E5FF").pack()
        self.create_next_button(self.show_step_4)

    def show_step_4(self):
        """ステップ4: 完了"""
        self.clear_container()
        self.create_header("FINAL STEP: INTEGRITY CHECK", "全ての防衛システムをオンラインにします。")
        bt_status = self.os_ctrl.check_bitlocker_status()
        ctk.CTkLabel(self.container, text=f"BITLOCKER: {bt_status}", text_color="#00FF41").pack(pady=5)
        ctk.CTkButton(self.container, text="FINALIZE & REBOOT CORE", command=self.finalize, height=50, fg_color="#FF003C", text_color="black", font=("Consolas", 16, "bold")).pack(pady=40, fill="x")

    def create_header(self, title, sub):
        ctk.CTkLabel(self.container, text=f"[ {title} ]", font=("Consolas", 24, "bold"), text_color="#FF003C").pack(pady=(0, 10))
        ctk.CTkLabel(self.container, text=sub, font=("MS Gothic", 12)).pack(pady=(0, 20))

    def create_next_button(self, cmd):
        ctk.CTkButton(self.container, text="NEXT >>>", command=cmd, fg_color="#1a1a1a", border_width=1, border_color="#FF003C", text_color="#00FF41", font=("Consolas", 14, "bold")).pack(pady=20)

    def clear_container(self):
        for widget in self.container.winfo_children(): widget.destroy()

    def finalize(self):
        ConfigManager.set("setup_complete", True)
        if self.on_complete: self.on_complete()
        self.destroy()

if __name__ == "__main__":
    root = ctk.CTk()
    SetupWizard(root, on_complete=lambda: root.destroy())
    root.mainloop()
