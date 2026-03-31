import customtkinter as ctk
from tkinter import messagebox
import hashlib
import time
import os
import logging
from config_manager import ConfigManager
from face_auth import FaceAuth
from os_control import OSRegistryController, is_admin

logger = logging.getLogger("SHINOBI.Wizard")

class SetupWizard(ctk.CTkToplevel):
    """
    SHINOBI 初回起動セットアップ・ウィザード。
    ステップバイステップでシステムの基本設定を行う。
    """
    def __init__(self, parent, on_complete=None):
        super().__init__(parent)
        self.title("SHINOBI - INITIAL SETUP WIZARD")
        self.geometry("700x500")
        self.configure(fg_color="#0D0D0D")
        self.attributes("-topmost", True)
        self.on_complete = on_complete
        self.step = 1

        self.face = FaceAuth()
        self.os_ctrl = OSRegistryController()

        # UIコンテナ
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(expand=True, fill="both", padx=40, pady=40)

        self.show_step_1()

    def show_step_1(self):
        """ステップ1: マスターPINの設定"""
        self.clear_container()

        ctk.CTkLabel(self.container, text="[ STEP 1: SET MASTER PIN ]", font=("Consolas", 24, "bold"), text_color="#FF003C").pack(pady=20)
        ctk.CTkLabel(self.container, text="システム解錠に使用する4桁以上のPINを設定してください。", font=("MS Gothic", 12)).pack(pady=10)

        self.pin_entry = ctk.CTkEntry(self.container, placeholder_text="New PIN", show="*", width=300, height=40, font=("Consolas", 18), justify="center")
        self.pin_entry.pack(pady=20)

        ctk.CTkButton(self.container, text="NEXT >>>", command=self.process_step_1, fg_color="#FF003C", hover_color="#CC0030", text_color="black", font=("Consolas", 14, "bold")).pack(pady=40)

    def process_step_1(self):
        pin = self.pin_entry.get()
        if len(pin) < 4:
            messagebox.showwarning("SHINOBI", "PINは4桁以上で設定してください。")
            return

        # ハッシュ化して保存
        pin_hash = hashlib.sha256(pin.encode()).hexdigest()
        ConfigManager.set("pin_hash", pin_hash)
        self.show_step_2()

    def show_step_2(self):
        """ステップ2: 顔データの登録"""
        self.clear_container()

        ctk.CTkLabel(self.container, text="[ STEP 2: BIOMETRIC SCAN ]", font=("Consolas", 24, "bold"), text_color="#FF003C").pack(pady=20)
        ctk.CTkLabel(self.container, text="顔をカメラに向けてください。特徴量をスキャンします。", font=("MS Gothic", 12)).pack(pady=10)

        self.scan_label = ctk.CTkLabel(self.container, text="WAITING FOR CAMERA...", font=("Consolas", 12), text_color="#00FF41")
        self.scan_label.pack(pady=20)

        ctk.CTkButton(self.container, text="START SCAN", command=self.process_step_2, fg_color="#FF003C", hover_color="#CC0030", text_color="black", font=("Consolas", 14, "bold")).pack(pady=40)

    def process_step_2(self):
        self.scan_label.configure(text="SCANNING... PLEASE WAIT...")
        self.update()

        # 実際にカメラを起動して登録
        if self.face.register_face("master_profile"):
            messagebox.showinfo("SHINOBI", "顔データの登録が完了しました。")
            self.show_step_3()
        else:
            messagebox.showerror("SHINOBI", "顔を検知できませんでした。もう一度お試しください。")
            self.scan_label.configure(text="SCAN FAILED. RETRYING...")

    def show_step_3(self):
        """ステップ3: システム整合性チェックと最終確認"""
        self.clear_container()

        ctk.CTkLabel(self.container, text="[ STEP 3: SYSTEM FINAL CHECK ]", font=("Consolas", 24, "bold"), text_color="#FF003C").pack(pady=20)

        # BitLocker確認
        bt_status = self.os_ctrl.check_bitlocker_status()
        bt_color = "#00FF41" if bt_status == "ON" else "#FF003C"
        ctk.CTkLabel(self.container, text=f"BitLocker Protection: {bt_status}", text_color=bt_color).pack(pady=5)

        # 管理者権限確認
        admin_status = "ELEVATED" if is_admin() else "RESTRICTED"
        admin_color = "#00FF41" if is_admin() else "#FF003C"
        ctk.CTkLabel(self.container, text=f"Admin Privilege: {admin_status}", text_color=admin_color).pack(pady=5)

        ctk.CTkLabel(self.container, text="全ての基本設定が完了しました。システムを起動します。", font=("MS Gothic", 12)).pack(pady=20)

        ctk.CTkButton(self.container, text="FINALIZE & REBOOT CORE", command=self.finalize, fg_color="#FF003C", hover_color="#CC0030", text_color="black", font=("Consolas", 14, "bold")).pack(pady=40)

    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def finalize(self):
        ConfigManager.set("setup_complete", True)
        if self.on_complete:
            self.on_complete()
        self.destroy()

if __name__ == "__main__":
    root = ctk.CTk()
    def finish():
        print("Wizard Completed.")
        root.destroy()
    wizard = SetupWizard(root, on_complete=finish)
    root.mainloop()
