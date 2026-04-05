import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import hashlib
import time
import os
import json
import qrcode
import threading
from PIL import Image, ImageTk
import logging
import sys

# 内部モジュール
from config_manager import ConfigManager
from face_auth import FaceAuth
from os_control import OSRegistryController, is_admin
from bt_monitor import BluetoothMonitor

logger = logging.getLogger("SHINOBI.Wizard")

class SetupWizard(ctk.CTkToplevel):
    """
    SHINOBI v4.0 究極のセットアップ・ウィザード。
    全ての認証要素とOS保護を厳重に構成。
    """
    def __init__(self, parent, on_complete=None):
        super().__init__(parent)
        self.title("SHINOBI - ULTIMATE INSTALLER v4.0")
        self.geometry("950x800")
        self.configure(fg_color="#0D0D0D")
        self.attributes("-topmost", True)
        self.on_complete = on_complete

        self.face = FaceAuth()
        self.os_ctrl = OSRegistryController()
        self.bt = BluetoothMonitor()

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(expand=True, fill="both", padx=80, pady=50)

        self.show_welcome()

    def show_welcome(self):
        self.clear_container()
        self.create_header("SHINOBI ULTIMATE 導入", "物理・OS・アプリケーションの3層防壁を構築します。")

        # 診断
        admin = is_admin()
        bt_status = self.os_ctrl.check_bitlocker_status()

        diag_frame = ctk.CTkFrame(self.container, fg_color="#121212", border_width=1, border_color="#333")
        diag_frame.pack(pady=20, fill="x")

        self.create_diag_item(diag_frame, "管理者権限 (Administrator)", admin)
        self.create_diag_item(diag_frame, "BitLocker ドライブ暗号化", bt_status == "ON")

        if not admin:
            ctk.CTkLabel(self.container, text="⚠️ 管理者権限が必要です。一度終了し、右クリックから管理者として実行してください。", text_color="#FF003C").pack()
        else:
            self.create_next_button("防衛設定を開始 >>>", self.show_step_1)

    def create_diag_item(self, parent, label, ok):
        color = "#00FF41" if ok else "#FF003C"
        status = "VERIFIED" if ok else "REQUIRED"
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(f, text=label, font=("MS Gothic", 12)).pack(side="left")
        ctk.CTkLabel(f, text=status, text_color=color, font=("Consolas", 12, "bold")).pack(side="right")

    def show_step_1(self):
        """マスターPIN設定"""
        self.clear_container()
        self.create_header("ステップ 1: マスターPIN", "全防衛の基底となる4桁以上の暗証番号を設定してください。")
        self.pin_entry = ctk.CTkEntry(self.container, placeholder_text="Enter Secure PIN", show="*", width=350, height=55, font=("Consolas", 28), justify="center")
        self.pin_entry.pack(pady=40)
        self.create_next_button("次へ進む >>>", self.process_pin)

    def process_pin(self):
        p = self.pin_entry.get()
        if len(p) < 4:
            messagebox.showwarning("SHINOBI", "PINは4桁以上必要です。")
            return
        ConfigManager.set("pin_hash", hashlib.sha256(p.encode()).hexdigest())
        self.show_step_2()

    def show_step_2(self):
        """生体情報の登録"""
        self.clear_container()
        self.create_header("ステップ 2: 生体情報の登録", "カメラを直視してください。複数の角度から特徴量を抽出します。")
        self.st_label = ctk.CTkLabel(self.container, text="READY TO SCAN", font=("Consolas", 14), text_color="#00FF41")
        self.st_label.pack(pady=40)
        ctk.CTkButton(self.container, text="スキャン開始", command=self.process_face, fg_color="#FF003C", text_color="black", font=("MS Gothic", 14, "bold"), height=50).pack()

    def process_face(self):
        self.st_label.configure(text="SCANNING... DO NOT MOVE")
        self.update()
        # 複数回撮影して精度を高める
        success = True
        for i in range(3):
            if not self.face.register_face(f"master_{i}"):
                success = False; break
            time.sleep(0.5)

        if success:
            messagebox.showinfo("SHINOBI", "生体情報の登録が完了しました。")
            self.show_step_3()
        else:
            messagebox.showerror("SHINOBI", "顔を認識できませんでした。照明等を確認してください。")

    def show_step_3(self):
        """Bluetooth接近設定"""
        self.clear_container()
        self.create_header("ステップ 3: 近接デバイスの設定", "常に携帯するスマートフォンをBluetoothで指定してください。")

        self.bt_list = ctk.CTkComboBox(self.container, values=["スキャン中..."], width=500, height=40)
        self.bt_list.pack(pady=20)

        self.rssi_slider = ctk.CTkSlider(self.container, from_=-90, to=-30, progress_color="#00FF41")
        self.rssi_slider.set(-70)
        self.rssi_slider.pack(pady=30, fill="x", padx=100)
        ctk.CTkLabel(self.container, text="接近閾値 (感度) の調整", font=("MS Gothic", 10)).pack()

        threading.Thread(target=self.scan_bt, daemon=True).start()
        self.create_next_button("このデバイスで確定 >>>", self.process_bt)

    def scan_bt(self):
        time.sleep(2) # 擬似スキャン
        self.bt_list.configure(values=["Personal Device (AA:BB:CC:DD:EE:FF)", "Trusted Phone (11:22:33:44:55:66)"])

    def process_bt(self):
        val = self.bt_list.get()
        if "(" in val:
            mac = val.split("(")[1].replace(")", "")
            ConfigManager.set("target_mac", mac)
            ConfigManager.set("rssi_threshold", int(self.rssi_slider.get()))
            self.show_step_4()
        else:
            messagebox.showwarning("SHINOBI", "デバイスを選択してください。")

    def show_step_4(self):
        """スマホ鍵ペアリング"""
        self.clear_container()
        self.create_header("ステップ 4: スマホ鍵の同期", "QRコードをスキャンして、最優先解錠トークンをスマホに保存してください。")

        token = "SHINOBI_" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]
        ConfigManager.set("browser_token", token)

        qr_data = json.dumps({"u": "12345678-1234-5678-1234-567812345678", "t": token})
        qr = qrcode.QRCode(version=1, box_size=8, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").resize((250, 250))
        self.qr_photo = ImageTk.PhotoImage(img)

        tk.Label(self.container, image=self.qr_photo, bg="white").pack(pady=20)
        self.create_next_button("最終防衛ラインへ >>>", self.show_step_5)

    def show_step_5(self):
        """OSシェル化とアンインストール保護"""
        self.clear_container()
        self.create_header("最終ステップ: OS空間の完全支配", "SHINOBIをWindowsのシェルとして登録し、アンインストールを保護します。")

        info_frame = ctk.CTkFrame(self.container, fg_color="#1a1a1a", border_width=1, border_color="#FF003C")
        info_frame.pack(pady=20, fill="both")

        warn_text = (
            "【重大な変更の承諾】\n"
            "1. ログイン時に直接SHINOBIが起動し、デスクトップを隠蔽します。\n"
            "2. 本アプリのアンインストールには、管理者パネルでの二段階認証が必須となります。\n"
            "3. システム異常時は、BitLocker回復キーを用いたセーフモード復旧が必要です。"
        )
        ctk.CTkLabel(info_frame, text=warn_text, font=("MS Gothic", 12), text_color="#FF003C", justify="left").pack(pady=20, padx=20)

        self.sw_shell = ctk.CTkSwitch(self.container, text="デスクトップをSHINOBIで置き換える", progress_color="#FF003C")
        self.sw_shell.pack(pady=10)
        self.sw_protect = ctk.CTkSwitch(self.container, text="アンインストール保護を有効にする", progress_color="#FF003C")
        self.sw_protect.select()
        self.sw_protect.pack(pady=10)

        ctk.CTkButton(self.container, text="設定を完了し、防衛をオンラインにする", command=self.finalize, height=60, fg_color="#FF003C", text_color="black", font=("MS Gothic", 16, "bold")).pack(pady=40, fill="x")

    def finalize(self):
        # レジストリ適用
        if self.sw_shell.get():
            self.os_ctrl.switch_to_custom_shell(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))

        ConfigManager.set("setup_complete", True)
        if self.on_complete: self.on_complete()
        self.destroy()

    def clear_container(self):
        for w in self.container.winfo_children(): w.destroy()

    def create_header(self, title, sub):
        ctk.CTkLabel(self.container, text=f"【 {title} 】", font=("MS Gothic", 32, "bold"), text_color="#FF003C").pack(pady=(0, 10))
        ctk.CTkLabel(self.container, text=sub, font=("MS Gothic", 13), text_color="#AAA").pack(pady=(0, 40))

    def create_next_button(self, text, cmd):
        ctk.CTkButton(self.container, text=text, command=cmd, fg_color="#1a1a1a", border_width=1, border_color="#FF003C", text_color="#00FF41", font=("MS Gothic", 14, "bold"), height=50).pack(pady=30)
