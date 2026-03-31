import asyncio
import sys
import os
import logging
import threading
import customtkinter as ctk

# 実行ファイルからの相対パスを正確に解決
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from mfa_engine import MFAEngine, SystemState
from bt_monitor import BluetoothMonitor
from face_auth import FaceAuth
from browser_key import BrowserKeyReceiver
from os_control import OSRegistryController, is_admin
from ui import ShinobiLockScreen, AdminDashboard
from audit_watchdog import AuditLog, Watchdog
from keyboard_hook import KeyboardHook
from config_manager import ConfigManager
from setup_wizard import SetupWizard

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("SHINOBI.Main")

class ShinobiApp:
    def __init__(self):
        ConfigManager.initialize()
        self.engine = MFAEngine()
        self.bt = BluetoothMonitor(target_mac=ConfigManager.get("target_mac"), rssi_threshold=ConfigManager.get("rssi_threshold"))
        self.face = FaceAuth(threshold=ConfigManager.get("face_threshold"))
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
        """全認証要素をバックグラウンドで並列監視。"""
        while True:
            if self.engine.state != SystemState.UNLOCKED:
                # 1. BT接近監視
                await self.bt.scan_nearby_devices()
                await self.engine.update_auth_factor("BT_NEARBY", self.bt.is_nearby())

                # 2. 顔認証監視 (非同期で実行、UIを止めない)
                # self.face.authenticate_async(lambda m, d: asyncio.run_coroutine_threadsafe(self.engine.update_auth_factor("FACE", m), self.loop))

            await asyncio.sleep(5) # 5秒間隔に短縮して応答性を向上

    def on_auth_success(self, route):
        logger.info(f"AUTHORIZED: {route}")
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
        logger.info("SHINOBI ULTIMATE v3.1 Starting...")
        self.os_ctrl.check_bitlocker_status()
        self.kb_hook.start()
        self.os_ctrl.set_lock_mode(True)

        self.async_thread.start()
        asyncio.run_coroutine_threadsafe(self.background_monitoring(), self.loop)
        asyncio.run_coroutine_threadsafe(self.engine.heartbeat_check(), self.loop)

        self.root = ctk.CTk()
        if not ConfigManager.get("setup_complete"):
            self.root.after(100, self.start_wizard)
        else:
            self.root.after(100, self.launch_lock_screen)

        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.kb_hook.stop()
            self.os_ctrl.set_lock_mode(False)

if __name__ == "__main__":
    app = ShinobiApp()
    app.run()
