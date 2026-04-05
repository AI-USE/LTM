import asyncio
import sys
import os
import logging
import threading
import customtkinter as ctk

# 正確なパス解決
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BUNDLE_DIR = os.path.join(BASE_DIR, "src")

if BUNDLE_DIR not in sys.path:
    sys.path.insert(0, BUNDLE_DIR)

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
        self.lock_screen = None
        self.loop = asyncio.new_event_loop()
        self.async_thread = threading.Thread(target=self.run_async_loop, daemon=True)

    def run_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def background_monitoring(self):
        """
        全認証要素を非同期に常時監視。
        """
        while True:
            if self.engine.state != SystemState.UNLOCKED:
                # 1. BT接近監視
                await self.bt.scan_nearby_devices()
                await self.engine.update_auth_factor("BT_NEARBY", self.bt.is_nearby())

                # 2. 顔認証（非同期）
                self.face.authenticate_async(self.on_face_match_result)

            await asyncio.sleep(5)

    def on_face_match_result(self, match, dist):
        """顔認証の結果を受け取り、MFAエンジンへ。"""
        if self.engine.state != SystemState.UNLOCKED:
            # スレッドセーフに実行
            asyncio.run_coroutine_threadsafe(self.engine.update_auth_factor("FACE", match), self.loop)

    def on_verified_token_callback(self, success):
        """スマホ鍵の結果を受け取り、MFAエンジンへ。"""
        if success and self.engine.state != SystemState.UNLOCKED:
            asyncio.run_coroutine_threadsafe(self.engine.update_auth_factor("BROWSER_KEY", True), self.loop)

    def on_auth_success(self, route):
        logger.info(f"認証成功、解錠します: {route}")
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
        logger.info("SHINOBI 起動中...")
        self.os_ctrl.check_bitlocker_status()
        self.kb_hook.start()
        self.os_ctrl.set_lock_mode(True)

        self.async_thread.start()
        asyncio.run_coroutine_threadsafe(self.background_monitoring(), self.loop)
        asyncio.run_coroutine_threadsafe(self.engine.heartbeat_check(), self.loop)
        # スマホ鍵待機開始
        asyncio.run_coroutine_threadsafe(self.browser_key.start_advertising(self.on_verified_token_callback), self.loop)

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
