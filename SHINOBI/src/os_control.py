import ctypes
import os
import platform
import logging
import subprocess
from tkinter import messagebox

logger = logging.getLogger("SHINOBI.OS")

def is_admin():
    try:
        if platform.system() == "Windows":
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        return os.getuid() == 0
    except: return False

class OSRegistryController:
    """
    Windowsの機能を厳重に封殺・復元する。
    """
    POLICY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"

    def __init__(self):
        self.restrictions = ["DisableTaskMgr", "DisableLockWorkstation", "DisableChangePassword", "DisableLogoff"]

    def check_bitlocker_status(self):
        """BitLocker保護状態を精密に確認。"""
        if platform.system() != "Windows": return "OFF (MOCK)"
        try:
            # 外部OS解析を防ぐため、TPMと連携した暗号化をチェック
            res = subprocess.check_output("manage-bde -status C:", shell=True, stderr=subprocess.STDOUT).decode('cp932', errors='ignore')
            if any(x in res for x in ["保護されています", "Protection On"]):
                logger.info("Drive Integrity: SECURE (BitLocker Active)")
                return "ON"
            return "OFF"
        except: return "ERROR"

    def set_lock_mode(self, enabled=True):
        """全てのOS抜け道を即座に封鎖。"""
        if platform.system() != "Windows" or not is_admin(): return
        import winreg
        val = 1 if enabled else 0
        try:
            key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, self.POLICY_PATH, 0, winreg.KEY_SET_VALUE)
            for r in self.restrictions:
                winreg.SetValueEx(key, r, 0, winreg.REG_DWORD, val)
            winreg.CloseKey(key)
            logger.info(f"Registry Hardening: {'ACTIVE' if enabled else 'INACTIVE'}")
        except Exception as e: logger.error(f"Registry operation failed: {e}")

    def switch_to_custom_shell(self, exe_path):
        """デスクトップをSHINOBIに置換。"""
        if platform.system() != "Windows" or not is_admin(): return
        import winreg
        try:
            # Winlogon Shell の変更
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "Shell", 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
            logger.info(f"Shell Migration: {exe_path}")
        except Exception as e: logger.error(f"Shell swap failed: {e}")

    def restore_explorer_shell(self):
        self.switch_to_custom_shell("explorer.exe")
