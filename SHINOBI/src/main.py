import asyncio
import sys
import os
import logging
import threading
import customtkinter as ctk

# パス解決
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BUNDLE_DIR = os.path.join(BASE_DIR, "src")

if BUNDLE_DIR not in sys.path: sys.path.insert(0, BUNDLE_DIR)

from mfa_engine import MFAEngine, SystemState
from bt_monitor import BluetoothMonitor
from face_auth import FaceAuth
from browser_key import BrowserKeyReceiver
from os_control import OSRegistryController, is_admin
from ui import ShinobiLockScreen, AdminDashboard
from audit_watchdog import AuditLog
from keyboard_hook import KeyboardHook
from config_manager import ConfigManager
from setup_wizard import SetupWizard

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] SHINOBI: %(message)s')
logger = logging.getLogger("SHINOBI.Main")

class ShinobiApp:
    """
    SHINOBI v4.0 究極版メイン。
    """
    def __init__(self):
        ConfigManager.initialize()
        self.engine = MFAEngine()
        self.bt = BluetoothMonitor()
        self.face = FaceAuth()
        self.browser_key = BrowserKeyReceiver()
        self.os_ctrl = OSRegistryController()
        self.audit = AuditLog()
        self.kb_hook = KeyboardHook()

        self.root = None
        self.loop = asyncio.new_event_loop()
        self.async_thread = threading.Thread(target=self.run_async_loop, daemon=True)

    def run_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def background_monitoring(self):
        """センサー並列監視。"""
        while True:
            if self.engine.state != SystemState.UNLOCKED:
                await self.bt.scan_nearby_devices()
                asyncio.run_coroutine_threadsafe(self.engine.update_auth_factor("BT_NEARBY", self.bt.is_nearby()), self.loop)
                self.face.authenticate_async(self.on_face_result)
            await asyncio.sleep(5)

    def on_face_result(self, m, d):
        if self.engine.state != SystemState.UNLOCKED:
            asyncio.run_coroutine_threadsafe(self.engine.update_auth_factor("FACE", m), self.loop)

    def on_token_verified(self, success):
        if success and self.engine.state != SystemState.UNLOCKED:
            asyncio.run_coroutine_threadsafe(self.engine.update_auth_factor("BROWSER_KEY", True), self.loop)

    def on_auth_success(self, route):
        logger.info(f"Access Granted: {route}")
        self.os_ctrl.set_lock_mode(False)
        self.kb_hook.stop()
        self.audit.log_entry(route)
        asyncio.run_coroutine_threadsafe(self.engine.unlock_system(route), self.loop)

    def start_wizard(self):
        wizard = SetupWizard(self.root, on_complete=self.launch_lock_screen)
        wizard.grab_set()

    def launch_lock_screen(self):
        self.lock_screen = ShinobiLockScreen(self.root, self.engine, on_auth_success=self.on_auth_success)

    def run(self):
        # 防御の有効化
        self.os_ctrl.check_bitlocker_status()
        self.kb_hook.start()
        self.os_ctrl.set_lock_mode(True)

        self.async_thread.start()
        asyncio.run_coroutine_threadsafe(self.background_monitoring(), self.loop)
        asyncio.run_coroutine_threadsafe(self.engine.heartbeat_check(), self.loop)
        asyncio.run_coroutine_threadsafe(self.browser_key.start_advertising(self.on_token_verified), self.loop)

        self.root = ctk.CTk()
        if not ConfigManager.get("setup_complete"):
            self.root.after(100, self.start_wizard)
        else:
            self.root.after(100, self.launch_lock_screen)

        try:
            self.root.mainloop()
        except Exception as e:
            logger.critical(f"FATAL ERROR: {e}")
            # 自己修復UI（最終窓口）を表示するチャンスがあればここで表示
        finally:
            self.kb_hook.stop()
            self.os_ctrl.set_lock_mode(False)

if __name__ == "__main__":
    ShinobiApp().run()
