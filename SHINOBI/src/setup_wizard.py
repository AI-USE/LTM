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
from bleak import BleakScanner

# 内部モジュール
from config_manager import ConfigManager
from face_auth import FaceAuth
from os_control import OSRegistryController, is_admin
from bt_monitor import BluetoothMonitor

logger = logging.getLogger("SHINOBI.Wizard")

class SetupWizard(ctk.CTkToplevel):
    """
    SHINOBI v4.1 究極のセットアップ・ウィザード。
    全モックを排除した実戦導入ガイダンス。
    """
    def __init__(self, parent, on_complete=None):
        super().__init__(parent)
        self.title("SHINOBI - ULTIMATE SETUP v4.1")
        self.geometry("900x750")
        self.configure(fg_color="#0D0D0D")
        self.attributes("-topmost", True)
        self.on_complete = on_complete

        self.face = FaceAuth()
        self.os_ctrl = OSRegistryController()
        self.bt_monitor = BluetoothMonitor()

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(expand=True, fill="both", padx=60, pady=40)

        self.show_welcome()

    def show_welcome(self):
        self.clear_container()
        self.create_header("WELCOME TO SHINOBI", "物理・OS・アプリの3層防壁を構築します。")

        admin = is_admin()
        bt_status = self.os_ctrl.check_bitlocker_status()

        diag = ctk.CTkFrame(self.container, fg_color="#121212", border_width=1, border_color="#333")
        diag.pack(pady=20, fill="x")
        self.create_diag(diag, "管理者特権", admin)
        self.create_diag(diag, "BitLocker暗号化", bt_status == "ON")

        if not admin:
            ctk.CTkLabel(self.container, text="⚠️ 続行するには管理者として実行し直す必要があります。", text_color="#FF003C").pack()
        else:
            self.create_next_button("防衛設定を開始 >>>", self.show_step_1)

    def create_diag(self, p, l, ok):
        f = ctk.CTkFrame(p, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(f, text=l, font=("MS Gothic", 12)).pack(side="left")
        ctk.CTkLabel(f, text="VERIFIED" if ok else "REQUIRED", text_color="#00FF41" if ok else "#FF003C", font=("Consolas", 12, "bold")).pack(side="right")

    def show_step_1(self):
        """マスターPIN設定"""
        self.clear_container()
        self.create_header("1. マスターPIN設定", "全ての鍵の種となる暗証番号を設定してください。")
        self.p_ent = ctk.CTkEntry(self.container, placeholder_text="New Master PIN", show="*", width=350, height=50, font=("Consolas", 24), justify="center")
        self.p_ent.pack(pady=30)
        self.create_next_button("顔認証の登録へ進む >>>", self.process_pin)

    def process_pin(self):
        p = self.p_ent.get()
        if len(p) < 4:
            messagebox.showwarning("SHINOBI", "PINは4桁以上必要です。")
            return
        ConfigManager.set("pin_hash", hashlib.sha256(p.encode()).hexdigest())
        self.show_step_2()

    def show_step_2(self):
        """生体登録 (実地スキャン)"""
        self.clear_container()
        self.create_header("2. 生体情報の登録", "カメラを直視してください。複数の角度から精密スキャンを行います。")
        self.st_lbl = ctk.CTkLabel(self.container, text="準備完了。スキャン中は動かないでください。", text_color="#00FF41")
        self.st_lbl.pack(pady=40)
        ctk.CTkButton(self.container, text="精密スキャンを開始", command=self.process_face, fg_color="#FF003C", text_color="black", height=50).pack()

    def process_face(self):
        self.st_lbl.configure(text="SCANNING ID... [ 0% ]")
        self.update()
        for i in range(3):
            if not self.face.register_face(f"master_{i}"):
                messagebox.showerror("SHINOBI", "顔を検出できませんでした。照明を確認してください。")
                return
            self.st_lbl.configure(text=f"SCANNING ID... [ {(i+1)*33}% ]")
            self.update(); time.sleep(0.5)
        messagebox.showinfo("SHINOBI", "生体情報の登録に成功しました。")
        self.show_step_3()

    def show_step_3(self):
        """Bluetooth設定 (実地スキャン)"""
        self.clear_container()
        self.create_header("3. 近接認証の設定", "連携するスマートフォンを検出します。")
        self.bt_list = ctk.CTkComboBox(self.container, values=["スキャン中..."], width=500, height=40)
        self.bt_list.pack(pady=20)

        self.sl = ctk.CTkSlider(self.container, from_=-90, to=-30, progress_color="#00FF41")
        self.sl.set(-70); self.sl.pack(pady=20, fill="x", padx=100)
        ctk.CTkLabel(self.container, text="接近検知感度の調整", font=("MS Gothic", 10)).pack()

        threading.Thread(target=self.scan_bt_hardware, daemon=True).start()
        self.create_next_button("このデバイスでロック >>>", self.process_bt)

    def scan_bt_hardware(self):
        """実際にハードウェアを使用してスキャンを行う。"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            devices = loop.run_until_complete(BleakScanner.discover(timeout=5.0))
            names = [f"{d.name or 'Unknown'} ({d.address})" for d in devices]
            if not names: names = ["デバイスが見つかりません。再試行してください。"]
            self.bt_list.configure(values=names)
            self.bt_list.set(names[0])
        except Exception as e:
            logger.error(f"Hardware scan error: {e}")
            self.bt_list.configure(values=["Bluetoothエラーが発生しました。"])

    def process_bt(self):
        val = self.bt_list.get()
        if "(" in val:
            mac = val.split("(")[1].replace(")", "")
            ConfigManager.set("target_mac", mac)
            ConfigManager.set("rssi_threshold", int(self.sl.get()))
            self.show_step_4()
        else:
            messagebox.showwarning("SHINOBI", "有効なデバイスを選択してください。")

    def show_step_4(self):
        """スマホ鍵同期"""
        self.clear_container()
        self.create_header("4. スマホ鍵の同期", "QRコードをスキャンし、最優先解錠トークンをスマホへ同期してください。")
        token = "SHINOBI_" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]
        ConfigManager.set("browser_token", token)
        qr_data = json.dumps({"u": "12345678-1234-5678-1234-567812345678", "t": token})
        qr = qrcode.QRCode(version=1, box_size=8, border=4)
        qr.add_data(qr_data); qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").resize((220, 220))
        self.qr_p = ImageTk.PhotoImage(img)
        tk.Label(self.container, image=self.qr_p, bg="white").pack(pady=10)
        self.create_next_button("最終防衛ラインへ >>>", self.show_step_5)

    def show_step_5(self):
        """OS支配"""
        self.clear_container()
        self.create_header("5. システム権限の委譲", "SHINOBIをWindowsのシェルとして登録します。")
        info = ctk.CTkFrame(self.container, fg_color="#1a1a1a", border_width=1, border_color="#FF003C")
        info.pack(pady=20, fill="both")
        txt = "【重要】\nこの設定を適用すると、ログイン直後に直接SHINOBIが起動し、\n認証をパスするまでデスクトップの使用が制限されます。"
        ctk.CTkLabel(info, text=txt, font=("MS Gothic", 12), text_color="#FF003C", justify="left").pack(pady=20, padx=20)
        self.sw = ctk.CTkSwitch(self.container, text="SHINOBIをカスタムシェルとして登録する", progress_color="#FF003C")
        self.sw.pack(pady=20)
        ctk.CTkButton(self.container, text="セットアップ完了", command=self.finalize, height=60, fg_color="#FF003C", text_color="black", font=("MS Gothic", 16, "bold")).pack(pady=40, fill="x")

    def finalize(self):
        if self.sw.get():
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
