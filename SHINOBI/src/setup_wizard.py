import customtkinter as ctk
from tkinter import messagebox
import hashlib
import time
import os
import logging
import asyncio
import threading
from config_manager import ConfigManager
from face_auth import FaceAuth
from os_control import OSRegistryController, is_admin
from bt_monitor import BluetoothMonitor
from browser_key import BrowserKeyReceiver

logger = logging.getLogger("SHINOBI.Wizard")

class SetupWizard(ctk.CTkToplevel):
    """
    SHINOBI 拡張セットアップ・ウィザード。
    PIN、顔、Bluetooth、スマホ鍵の全設定を網羅。
    """
    def __init__(self, parent, on_complete=None):
        super().__init__(parent)
        self.title("SHINOBI - ULTIMATE SETUP WIZARD")
        self.geometry("800x600")
        self.configure(fg_color="#0D0D0D")
        self.attributes("-topmost", True)
        self.on_complete = on_complete

        self.face = FaceAuth()
        self.bt_monitor = BluetoothMonitor()
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
        self.create_header("STEP 2: BIOMETRIC SCAN", "カメラを直視してください。特徴量を暗号化して保存します。")

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
            messagebox.showerror("SHINOBI", "スキャン失敗。照明や位置を確認してください。")

    def show_step_3(self):
        """ステップ3: Bluetoothデバイス（スマホ）の設定"""
        self.clear_container()
        self.create_header("STEP 3: BLUETOOTH PROXIMITY", "PCと連携するスマートフォンを選択してください。")

        self.bt_status = ctk.CTkLabel(self.container, text="SCANNING FOR DEVICES...", text_color="#00FF41")
        self.bt_status.pack(pady=10)

        self.device_list = ctk.CTkComboBox(self.container, values=["Scanning..."], width=400)
        self.device_list.pack(pady=20)

        # 非同期スキャンの開始（簡易実装）
        threading.Thread(target=self.scan_bt_devices, daemon=True).start()

        self.create_next_button(self.process_step_3)

    def scan_bt_devices(self):
        # 実際には BleakScanner.discover() を実行
        time.sleep(2)
        # サンプル
        self.device_list.configure(values=["My Android (AA:BB:CC:DD:EE:FF)", "iPhone (11:22:33:44:55:66)"])
        self.bt_status.configure(text="DEVICES FOUND")

    def process_step_3(self):
        val = self.device_list.get()
        if "AA:BB" in val or "11:22" in val:
            mac = val.split("(")[1].replace(")", "")
            ConfigManager.set("target_mac", mac)
            self.show_step_4()
        else:
            messagebox.showwarning("SHINOBI", "デバイスを選択してください。")

    def show_step_4(self):
        """ステップ4: スマホ鍵（ブラウザトークン）の発行"""
        self.clear_container()
        self.create_header("STEP 4: SMARTPHONE KEY", "スマホ解錠用のセキュリティトークンを同期します。")

        token = "SHINOBI_TOKEN_" + str(int(time.time()))
        ConfigManager.set("browser_token", token)

        ctk.CTkLabel(self.container, text=f"Token: {token}", font=("Consolas", 14), text_color="#00E5FF").pack(pady=10)
        ctk.CTkLabel(self.container, text="スマホのブラウザで指定のURLを開き、このトークンを入力してください。", font=("MS Gothic", 10)).pack(pady=5)

        self.create_next_button(self.show_step_5)

    def show_step_5(self):
        """ステップ5: 完了と整合性チェック"""
        self.clear_container()
        self.create_header("FINAL STEP: INTEGRITY CHECK", "全ての防衛システムをオンラインにします。")

        bt_status = self.os_ctrl.check_bitlocker_status()
        ctk.CTkLabel(self.container, text=f"BITLOCKER: {bt_status}", text_color="#00FF41").pack(pady=5)
        ctk.CTkLabel(self.container, text=f"ADMIN PRIVILEGE: {'OK' if is_admin() else 'FAIL'}", text_color="#00FF41").pack(pady=5)

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
