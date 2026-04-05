import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import hashlib
import time
import os
import json
import qrcode
import threading
import asyncio
from PIL import Image, ImageTk
import logging

# 内部モジュール
from config_manager import ConfigManager
from face_auth import FaceAuth
from os_control import OSRegistryController, is_admin
from bt_monitor import BluetoothMonitor

logger = logging.getLogger("SHINOBI.Wizard")

class SetupWizard(ctk.CTkToplevel):
    """
    SHINOBI 究極版セットアップ・ウィザード。
    全てのセキュリティレイヤーを対話的に構成する。
    """
    def __init__(self, parent, on_complete=None):
        super().__init__(parent)
        self.title("SHINOBI - ULTIMATE SETUP v3.5")
        self.geometry("900x750")
        self.configure(fg_color="#0D0D0D")
        self.attributes("-topmost", True)
        self.on_complete = on_complete

        self.face = FaceAuth()
        self.os_ctrl = OSRegistryController()
        self.bt_monitor = BluetoothMonitor()
        self.scanning_bt = False

        # メインフレーム
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(expand=True, fill="both", padx=60, pady=40)

        self.show_welcome()

    def show_welcome(self):
        """導入とBitLocker確認"""
        self.clear_container()
        self.create_header("WELCOME TO SHINOBI", "究極の個人認証システムへようこそ。導入を開始します。")

        # BitLocker状態
        status = self.os_ctrl.check_bitlocker_status()
        color = "#00FF41" if status == "ON" else "#FF003C"
        status_text = "BitLocker保護: 有効 (推奨設定)" if status == "ON" else "BitLocker保護: 無効 (⚠️ 外部からの解析リスクがあります)"

        status_box = ctk.CTkFrame(self.container, fg_color="#1a1a1a", border_width=1, border_color=color)
        status_box.pack(pady=20, fill="x", padx=40)
        ctk.CTkLabel(status_box, text=status_text, font=("MS Gothic", 12), text_color=color).pack(pady=15)

        if status != "ON":
            ctk.CTkLabel(self.container, text="※最高レベルのセキュリティを確保するため、コントロールパネルから\nBitLockerを有効にすることを強く推奨します。", font=("MS Gothic", 10)).pack()

        self.create_next_button("防衛設定を開始 >>>", self.show_step_1)

    def show_step_1(self):
        """マスターPIN設定"""
        self.clear_container()
        self.create_header("1. マスターPINの設定", "最下層の鍵となる暗証番号を設定してください。")
        self.pin_entry = ctk.CTkEntry(self.container, placeholder_text="New Master PIN", show="*", width=350, height=50, font=("Consolas", 24), justify="center")
        self.pin_entry.pack(pady=30)
        self.create_next_button("次へ進む >>>", self.process_pin)

    def process_pin(self):
        pin = self.pin_entry.get()
        if len(pin) < 4:
            messagebox.showwarning("SHINOBI", "PINは4桁以上で設定してください。")
            return
        ConfigManager.set("pin_hash", hashlib.sha256(pin.encode()).hexdigest())
        self.show_step_2()

    def show_step_2(self):
        """顔認証の登録"""
        self.clear_container()
        self.create_header("2. 生体情報の登録", "カメラによる顔の特徴量スキャンを行います。")
        self.scan_status = ctk.CTkLabel(self.container, text="準備完了。カメラを直視してください。", font=("MS Gothic", 14), text_color="#00FF41")
        self.scan_status.pack(pady=40)
        ctk.CTkButton(self.container, text="スキャンを開始", command=self.process_face, fg_color="#FF003C", text_color="black", font=("MS Gothic", 14, "bold")).pack(pady=20)

    def process_face(self):
        self.scan_status.configure(text="スキャン中... 動かないでください")
        self.update()
        if self.face.register_face("master"):
            messagebox.showinfo("SHINOBI", "生体プロファイルの登録に成功しました。")
            self.show_step_3()
        else:
            messagebox.showerror("SHINOBI", "顔を検知できませんでした。")

    def show_step_3(self):
        """Bluetooth接近感度設定"""
        self.clear_container()
        self.create_header("3. 近接認証の設定", "Bluetoothデバイス（スマホ等）の検知感度を調整します。")

        self.bt_list = ctk.CTkComboBox(self.container, values=["デバイスを検索中..."], width=450)
        self.bt_list.pack(pady=10)

        self.rssi_label = ctk.CTkLabel(self.container, text="接近閾値 (dBm): -70", font=("Consolas", 12), text_color="#00E5FF")
        self.rssi_label.pack(pady=10)

        self.rssi_slider = ctk.CTkSlider(self.container, from_=-90, to=-30, progress_color="#00FF41", command=self.update_rssi_text)
        self.rssi_slider.set(-70)
        self.rssi_slider.pack(pady=10, fill="x", padx=100)

        ctk.CTkLabel(self.container, text="-90 (広範囲) <-----> -30 (超至近距離)", font=("Consolas", 10)).pack()

        # スキャンの開始
        if not self.scanning_bt:
            self.scanning_bt = True
            threading.Thread(target=self.scan_bt, daemon=True).start()

        self.create_next_button("この設定で同期 >>>", self.process_bt)

    def update_rssi_text(self, val):
        self.rssi_label.configure(text=f"接近閾値 (dBm): {int(val)}")

    def scan_bt(self):
        # 実際には BleakScanner
        time.sleep(2)
        self.bt_list.configure(values=["iPhone (11:22:33:44:55:66)", "Android (AA:BB:CC:DD:EE:FF)"])

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
        """スマホ鍵の発行"""
        self.clear_container()
        self.create_header("4. スマホ鍵の同期", "QRコードをスキャンして、1要素解錠用トークンを取得してください。")

        token = "SHINOBI_" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]
        ConfigManager.set("browser_token", token)

        qr_str = json.dumps({"u": "12345678-1234-5678-1234-567812345678", "c": "87654321-4321-8765-4321-876543210987", "t": token})
        qr = qrcode.QRCode(version=1, box_size=8, border=4)
        qr.add_data(qr_str)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").resize((220, 220))
        self.qr_img = ImageTk.PhotoImage(img)

        tk.Label(self.container, image=self.qr_img, bg="white").pack(pady=10)
        self.create_next_button("最終確認へ進む >>>", self.show_step_5)

    def show_step_5(self):
        """OSレベルのデスクトップ置き換え（シェル化）許可"""
        self.clear_container()
        self.create_header("5. システム権限の委譲", "SHINOBIを唯一の操作インターフェースとして登録します。")

        info_text = (
            "【警告】\nこの操作を行うと、PC起動時に直接デスクトップが表示されず、\n"
            "SHINOBIのロック画面が最前面に表示されるようになります。\n"
            "万が一の解錠不能時はセーフモードでのリカバリが必要となります。"
        )
        info_box = ctk.CTkFrame(self.container, fg_color="#1a1a1a", border_width=1, border_color="#FF003C")
        info_box.pack(pady=20, fill="both", padx=40)
        ctk.CTkLabel(info_box, text=info_text, font=("MS Gothic", 12), text_color="#FF003C", justify="left").pack(pady=20, padx=20)

        self.shell_switch = ctk.CTkSwitch(self.container, text="SHINOBIをカスタムシェルとして登録する (Winlogon)", progress_color="#FF003C")
        self.shell_switch.pack(pady=20)

        ctk.CTkButton(self.container, text="セットアップを完了して起動", command=self.finalize, height=60, fg_color="#FF003C", text_color="black", font=("MS Gothic", 18, "bold")).pack(pady=30, fill="x")

    def finalize(self):
        if self.shell_switch.get():
            self.os_ctrl.switch_to_custom_shell(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))

        ConfigManager.set("setup_complete", True)
        if self.on_complete: self.on_complete()
        self.destroy()

    def clear_container(self):
        for w in self.container.winfo_children(): w.destroy()

    def create_header(self, title, sub):
        ctk.CTkLabel(self.container, text=f"【 {title} 】", font=("MS Gothic", 28, "bold"), text_color="#FF003C").pack(pady=(0, 10))
        ctk.CTkLabel(self.container, text=sub, font=("MS Gothic", 12), text_color="#AAA").pack(pady=(0, 30))

    def create_next_button(self, text, cmd):
        ctk.CTkButton(self.container, text=text, command=cmd, fg_color="#1a1a1a", border_width=1, border_color="#FF003C", text_color="#00FF41", font=("MS Gothic", 14, "bold"), height=45).pack(pady=20)

if __name__ == "__main__":
    import sys
    root = ctk.CTk()
    SetupWizard(root, on_complete=lambda: root.destroy())
    root.mainloop()
