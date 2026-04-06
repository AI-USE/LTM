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
import sys

try:
    from config_manager import ConfigManager
    from face_auth import FaceAuth
    from os_control import OSRegistryController, is_admin
    from bt_monitor import BluetoothMonitor
except ImportError:
    from .config_manager import ConfigManager
    from .face_auth import FaceAuth
    from .os_control import OSRegistryController, is_admin
    from .bt_monitor import BluetoothMonitor

logger = logging.getLogger("SHINOBI.Wizard")

class SetupWizard(ctk.CTkToplevel):
    """
    SHINOBI v4.2 初期設定ウィザード (極致日本語版)。
    """
    def __init__(self, parent, on_complete=None):
        super().__init__(parent)
        self.title("SHINOBI - 最終防衛システム導入ガイダンス")
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
        self.create_header("SHINOBI ULTIMATE 導入開始", "物理、OS、アプリケーションの三層に渡る防壁を構築します。")

        admin = is_admin()
        bt_status = self.os_ctrl.check_bitlocker_status()

        diag = ctk.CTkFrame(self.container, fg_color="#121212", border_width=1, border_color="#333")
        diag.pack(pady=20, fill="x")
        self.create_diag(diag, "システム特権 (管理者権限)", admin)
        self.create_diag(diag, "物理層暗号化 (BitLocker)", bt_status == "ON")

        if not admin:
            ctk.CTkLabel(self.container, text="⚠️ 管理者権限が不足しています。右クリックから「管理者として実行」してください。", text_color="#FF003C", font=("MS Gothic", 12)).pack()
        else:
            self.create_next_button("防衛プロトコルを開始する >>>", self.show_step_1)

    def create_diag(self, p, l, ok):
        f = ctk.CTkFrame(p, fg_color="transparent")
        f.pack(fill="x", padx=25, pady=12)
        ctk.CTkLabel(f, text=l, font=("MS Gothic", 13)).pack(side="left")
        ctk.CTkLabel(f, text="検証完了" if ok else "要設定", text_color="#00FF41" if ok else "#FF003C", font=("MS Gothic", 13, "bold")).pack(side="right")

    def show_step_1(self):
        self.clear_container()
        self.create_header("1. マスターPINの刻印", "全防衛レイヤーの基底となる4桁以上の暗証番号を設定してください。")
        self.p_ent = ctk.CTkEntry(self.container, placeholder_text="新しいマスターPINを入力", show="*", width=350, height=55, font=("Consolas", 28), justify="center")
        self.p_ent.pack(pady=40)
        self.create_next_button("生体情報の登録へ進む >>>", self.process_pin)

    def process_pin(self):
        p = self.p_ent.get()
        if len(p) < 4:
            messagebox.showwarning("SHINOBI", "暗証番号は4桁以上で設定してください。")
            return
        ConfigManager.set("pin_hash", hashlib.sha256(p.encode()).hexdigest())
        self.show_step_2()

    def show_step_2(self):
        self.clear_container()
        self.create_header("2. 生体プロファイルの作成", "カメラを直視してください。複数の角度から顔の特徴を精密に抽出します。")
        self.st_lbl = ctk.CTkLabel(self.container, text="スキャン準備完了。照明が十分な場所で行ってください。", font=("MS Gothic", 14), text_color="#00FF41")
        self.st_lbl.pack(pady=40)
        ctk.CTkButton(self.container, text="精密スキャンを開始", command=self.process_face, fg_color="#FF003C", text_color="black", font=("MS Gothic", 15, "bold"), height=55, width=300).pack()

    def process_face(self):
        self.st_lbl.configure(text="解析中... 動かないでください")
        self.update()

        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW if os.name == 'nt' else 0)
        if not cap.isOpened():
            messagebox.showerror("SHINOBI", "カメラにアクセスできません。")
            return

        success_count = 0
        try:
            for i in range(3):
                # 安定させるために数フレーム飛ばす
                for _ in range(5): cap.read()
                ret, frame = cap.read()
                if ret and self.face.register_face(frame):
                    success_count += 1
                    self.st_lbl.configure(text=f"解析中... {int((i+1)*33)}% 完了")
                    self.update()
                time.sleep(0.5)
        finally:
            cap.release()

        if success_count >= 1:
            messagebox.showinfo("SHINOBI", "生体情報の登録に成功しました。")
            self.show_step_3()
        else:
            messagebox.showerror("SHINOBI", "顔を認識できませんでした。カメラとの距離や照明を調整してください。")

    def show_step_3(self):
        self.clear_container()
        self.create_header("3. 近接認証デバイスの指定", "常に携帯するスマートフォンをBluetoothでスキャンし、紐付けます。")
        self.bt_list = ctk.CTkComboBox(self.container, values=["スキャン中..."], width=550, height=45, font=("MS Gothic", 12))
        self.bt_list.pack(pady=20)
        self.sl = ctk.CTkSlider(self.container, from_=-90, to=-30, progress_color="#00FF41")
        self.sl.set(-70); self.sl.pack(pady=30, fill="x", padx=100)
        ctk.CTkLabel(self.container, text="検知感度（RSSI）の調整", font=("MS Gothic", 11), text_color="#AAA").pack()

        def scan_task():
            from bleak import BleakScanner
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                devs = loop.run_until_complete(BleakScanner.discover(timeout=5.0))
                names = [f"{d.name or '不明なデバイス'} ({d.address})" for d in devs]
                if not names: names = ["デバイスが見つかりません。再試行してください。"]
                self.bt_list.configure(values=names); self.bt_list.set(names[0])
            except: self.bt_list.configure(values=["Bluetooth機能にアクセスできません。"])

        threading.Thread(target=scan_task, daemon=True).start()
        self.create_next_button("このデバイスを信頼する >>>", self.process_bt)

    def process_bt(self):
        val = self.bt_list.get()
        if "(" in val:
            mac = val.split("(")[1].replace(")", "")
            ConfigManager.set("target_mac", mac)
            ConfigManager.set("rssi_threshold", int(self.sl.get()))
            self.show_step_4()
        else: messagebox.showwarning("SHINOBI", "有効なデバイスを選択してください。")

    def show_step_4(self):
        self.clear_container()
        self.create_header("4. スマホ鍵の同期", "QRコードをスキャンして、最優先の解錠権限をスマホへ保存してください。")
        token = "SHINOBI_" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]
        ConfigManager.set("browser_token", token)
        qr_data = json.dumps({"u": "12345678-1234-5678-1234-567812345678", "t": token})
        qr = qrcode.QRCode(version=1, box_size=8, border=4)
        qr.add_data(qr_data); qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").resize((240, 240))
        self.qr_p = ImageTk.PhotoImage(img)
        tk.Label(self.container, image=self.qr_p, bg="white").pack(pady=15)
        self.create_next_button("最終セキュリティ確認へ >>>", self.show_step_5)

    def show_step_5(self):
        self.clear_container()
        self.create_header("5. システム権限の委譲", "SHINOBIをWindowsの正式なシェルとして登録し、デスクトップを完全保護します。")
        info = ctk.CTkFrame(self.container, fg_color="#1a1a1a", border_width=1, border_color="#FF003C")
        info.pack(pady=25, fill="both")
        txt = "【重要事項の承諾】\n・ログイン直後に本システムが起動し、認証までデスクトップは表示されません。\n・本システムのアンインストールには、管理者パネルでの二段階認証が必須です。\n・異常時はBitLocker回復キーを用いたセーフモード復旧が必要です。"
        ctk.CTkLabel(info, text=txt, font=("MS Gothic", 12), text_color="#FF003C", justify="left").pack(pady=25, padx=25)
        self.sw = ctk.CTkSwitch(self.container, text="WindowsデスクトップをSHINOBIで完全秘匿する", progress_color="#FF003C", font=("MS Gothic", 12))
        self.sw.pack(pady=20)
        ctk.CTkButton(self.container, text="全ての防衛を有効化する", command=self.finalize, height=65, fg_color="#FF003C", text_color="black", font=("MS Gothic", 18, "bold")).pack(pady=40, fill="x")

    def finalize(self):
        if self.sw.get():
            # 本番環境ではメインの実行ファイルをシェルに指定
            exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
            self.os_ctrl.switch_to_custom_shell(exe_path)
        ConfigManager.set("setup_complete", True)
        if self.on_complete: self.on_complete()
        self.destroy()

    def clear_container(self):
        for w in self.container.winfo_children(): w.destroy()

    def create_header(self, title, sub):
        ctk.CTkLabel(self.container, text=f"【 {title} 】", font=("MS Gothic", 34, "bold"), text_color="#FF003C").pack(pady=(0, 15))
        ctk.CTkLabel(self.container, text=sub, font=("MS Gothic", 14), text_color="#BBB").pack(pady=(0, 45))

    def create_next_button(self, text, cmd):
        ctk.CTkButton(self.container, text=text, command=cmd, fg_color="#1a1a1a", border_width=1, border_color="#FF003C", text_color="#00FF41", font=("MS Gothic", 15, "bold"), height=55, width=350).pack(pady=35)
