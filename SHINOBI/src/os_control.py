import ctypes
import os
import platform
import logging
import subprocess
from tkinter import messagebox

# ロギング設定
logger = logging.getLogger("SHINOBI.OS")

def is_admin():
    """
    Windows上で管理者権限（Admin）があるか確認。
    """
    try:
        if platform.system() == "Windows":
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        return os.getuid() == 0 if hasattr(os, 'getuid') else False
    except Exception:
        return False

class OSRegistryController:
    """
    Windowsのレジストリを操作し、機能を制限/復元するクラス。
    """
    POLICY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"

    def __init__(self):
        self.restrictions = ["DisableTaskMgr", "DisableLockWorkstation", "DisableChangePassword", "DisableLogoff"]

    def check_bitlocker_status(self):
        """
        BitLockerの状態を確認 (manage-bde 使用)。
        """
        if platform.system() != "Windows":
            return "N/A (MOCK)"

        try:
            # 管理者権限で manage-bde -status を実行
            # ※日本語環境と英語環境の両方を想定
            result = subprocess.check_output(["manage-bde", "-status", "C:"], shell=True, stderr=subprocess.STDOUT).decode('cp932', errors='ignore')
            if any(x in result for x in ["保護されています", "Protection On", "Encryption On"]):
                logger.info("BitLocker Protection: ON (Verified)")
                return "ON"
            else:
                logger.warning("BitLocker Protection: OFF (SECURITY WARNING)")
                return "OFF"
        except Exception as e:
            logger.error(f"Failed to check BitLocker status: {e}")
            return "ERROR"

    def set_lock_mode(self, enabled=True):
        """
        レジストリ制限の切り替え。
        """
        if platform.system() != "Windows":
            logger.info(f"[MOCK] Registry set_lock_mode: {'ENABLED' if enabled else 'DISABLED'}")
            return

        if not is_admin():
            logger.error("Registry modify failed: Admin privileges required.")
            return

        import winreg
        value = 1 if enabled else 0
        try:
            key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, self.POLICY_PATH, 0, winreg.KEY_SET_VALUE)
            for reg_name in self.restrictions:
                winreg.SetValueEx(key, reg_name, 0, winreg.REG_DWORD, value)
            winreg.CloseKey(key)
            logger.info(f"Registry restrictions {'applied' if enabled else 'cleared'}.")
        except Exception as e:
            logger.error(f"Failed to update registry: {e}")

    def switch_to_custom_shell(self, exe_path):
        """
        Windowsのシェルを explorer.exe から本アプリに変更する。
        """
        SHELL_REG_PATH = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
        if platform.system() != "Windows":
            logger.info(f"[MOCK] Switch Shell to: {exe_path}")
            return

        if not is_admin():
            logger.error("Shell change failed: Admin privileges required.")
            return

        # ⚠️ 危険な操作のため、ユーザーに最終確認
        if not messagebox.askyesno("SHINOBI - 警告",
            "Windowsシェルを変更しますか？\n不具合が発生した場合、デスクトップが表示されなくなるリスクがあります。\n(リカバリ手順を熟知している場合のみ実行してください)"):
            logger.info("Shell change cancelled by user.")
            return

        import winreg
        try:
            # バックアップ作成
            key_read = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, SHELL_REG_PATH, 0, winreg.KEY_READ)
            old_shell, _ = winreg.QueryValueEx(key_read, "Shell")
            winreg.CloseKey(key_read)
            logger.info(f"Current shell backup: {old_shell}")

            # 新しいシェルを設定
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, SHELL_REG_PATH, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "Shell", 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
            logger.info(f"Custom shell set to: {exe_path}")
            messagebox.showinfo("SHINOBI", f"シェルを {exe_path} に変更しました。\n次回のログインから有効になります。")
        except Exception as e:
            logger.error(f"Failed to change shell: {e}")
            messagebox.showerror("SHINOBI", f"シェル変更エラー: {e}")

    def restore_explorer_shell(self):
        """
        シェルを標準の explorer.exe に戻す。
        """
        if platform.system() == "Windows":
            self.switch_to_custom_shell("explorer.exe")
        else:
            logger.info("[MOCK] Restore explorer shell.")
