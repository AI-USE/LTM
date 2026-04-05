import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import hashlib
import time
import os
import qrcode
from PIL import Image, ImageTk
import logging
import json
from config_manager import ConfigManager
from face_auth import FaceAuth
from os_control import OSRegistryController, is_admin

logger = logging.getLogger("SHINOBI.Wizard")

class SetupWizard(ctk.CTkToplevel):
    """
    SHINOBI 初期セットアップ・ウィザード (完全日本語版)。
    """
    def __init__(self, parent, on_complete=None):
        super().__init__(parent)
        self.title("SHINOBI - 初期設定ウィザード")
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
        self.create_header("ステップ 1: マスターPINの設定", "システム解錠に使用する4桁以上の暗証番号を設定してください。")
        self.pin_entry = ctk.CTkEntry(self.container, placeholder_text="新しいPINを入力", show="*", width=300, height=45, font=("MS Gothic", 20), justify="center")
        self.pin_entry.pack(pady=20)
        self.create_next_button("次へ進む >>>", self.process_step_1)

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
        self.create_header("ステップ 2: 生体情報の登録", "カメラを直視してください。あなたの顔の特徴を暗号化して保存します。")
        self.scan_label = ctk.CTkLabel(self.container, text="ステータス: 準備完了", font=("MS Gothic", 14), text_color="#00FF41")
        self.scan_label.pack(pady=30)
        ctk.CTkButton(self.container, text="顔スキャンを開始", command=self.process_step_2, fg_color="#FF003C", text_color="black", font=("MS Gothic", 14, "bold")).pack(pady=20)

    def process_step_2(self):
        self.scan_label.configure(text="スキャン中... 動かないでください")
        self.update()
        if self.face.register_face("master"):
            messagebox.showinfo("SHINOBI", "顔認証の設定が完了しました。")
            self.show_step_3()
        else:
            messagebox.showerror("SHINOBI", "スキャンに失敗しました。カメラを確認してください。")

    def show_step_3(self):
        """ステップ3: スマホ鍵の同期"""
        self.clear_container()
        self.create_header("ステップ 3: スマホ鍵のペアリング", "スマホのブラウザでこのQRコードを読み取り、解錠トークンを同期してください。")

        token = "SHINOBI_" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]
        ConfigManager.set("browser_token", token)

        qr_data = {
            "u": "12345678-1234-5678-1234-567812345678",
            "c": "87654321-4321-8765-4321-876543210987",
            "t": token
        }
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").resize((250, 250))
        self.qr_photo = ImageTk.PhotoImage(img)

        tk.Label(self.container, image=self.qr_photo, bg="white").pack(pady=10)
        ctk.CTkLabel(self.container, text=f"秘密トークン: {token}", font=("Consolas", 10), text_color="#00E5FF").pack()
        self.create_next_button("次へ進む >>>", self.show_step_4)

    def show_step_4(self):
        """ステップ4: 最終整合性チェック"""
        self.clear_container()
        self.create_header("最終ステップ: 防衛システムの起動", "全ての防衛レイヤーをオンラインにします。")
        bt_status = self.os_ctrl.check_bitlocker_status()
        ctk.CTkLabel(self.container, text=f"BitLocker保護: {'有効' if bt_status=='ON' else '無効'}", text_color="#00FF41", font=("MS Gothic", 14)).pack(pady=5)
        ctk.CTkLabel(self.container, text=f"管理者権限: {'取得済み' if is_admin() else '未取得'}", text_color="#00FF41", font=("MS Gothic", 14)).pack(pady=5)
        ctk.CTkButton(self.container, text="設定を完了して起動", command=self.finalize, height=50, fg_color="#FF003C", text_color="black", font=("MS Gothic", 16, "bold")).pack(pady=40, fill="x")

    def create_header(self, title, sub):
        ctk.CTkLabel(self.container, text=f"【 {title} 】", font=("MS Gothic", 24, "bold"), text_color="#FF003C").pack(pady=(0, 10))
        ctk.CTkLabel(self.container, text=sub, font=("MS Gothic", 12)).pack(pady=(0, 20))

    def create_next_button(self, text, cmd):
        ctk.CTkButton(self.container, text=text, command=cmd, fg_color="#1a1a1a", border_width=1, border_color="#FF003C", text_color="#00FF41", font=("MS Gothic", 14, "bold")).pack(pady=20)

    def clear_container(self):
        for widget in self.container.winfo_children(): widget.destroy()

    def finalize(self):
        ConfigManager.set("setup_complete", True)
        if self.on_complete: self.on_complete()
        self.destroy()
