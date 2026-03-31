import ctypes
import os
import platform
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("SHINOBI")

def is_admin():
    """
    Windows上で管理者権限（Admin）があるか確認。
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        # Linux/Mac環境などでのフォールバック
        return os.getuid() == 0 if hasattr(os, 'getuid') else False

class OSRegistryController:
    """
    Windowsのレジストリを操作し、機能を制限/復元するクラス。
    権限チェックを伴う。
    """
    POLICY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"

    def __init__(self):
        self.restrictions = ["DisableTaskMgr", "DisableLockWorkstation", "DisableChangePassword", "DisableLogoff"]

    def set_lock_mode(self, enabled=True):
        if platform.system() != "Windows":
            logger.info(f"[MOCK] Registry set_lock_mode: {'ENABLED' if enabled else 'DISABLED'}")
            return

        if not is_admin():
            logger.error("Admin privileges required to modify registry.")
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
        SHELL_REG_PATH = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
        if platform.system() != "Windows":
            logger.info(f"[MOCK] Switch Shell to: {exe_path}")
            return

        if not is_admin():
            logger.error("Admin privileges required to change Windows shell.")
            return

        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, SHELL_REG_PATH, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "Shell", 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
            logger.info(f"Custom shell set to: {exe_path}")
        except Exception as e:
            logger.error(f"Failed to change shell: {e}")

    def restore_explorer_shell(self):
        self.switch_to_custom_shell("explorer.exe")
