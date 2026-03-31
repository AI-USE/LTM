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

# 自作モジュールのインポート
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
    """
    SHINOBI 究極個人認証システム v3.1
    """
    def __init__(self):
        ConfigManager.initialize()
        self.engine = MFAEngine()
        self.bt = BluetoothMonitor(target_mac=ConfigManager.get("target_mac"), rssi_threshold=ConfigManager.get("rssi_threshold"))
        self.face = FaceAuth(threshold=ConfigManager.get("face_threshold"))
        self.browser_key = BrowserKeyReceiver()
        self.os_ctrl = OSRegistryController()
        self.audit = AuditLog()
        self.kb_hook = KeyboardHook()
        self.watchdog = Watchdog()

        self.root = None
        self.loop = asyncio.new_event_loop()
        self.async_thread = threading.Thread(target=self.run_async_loop, daemon=True)

    def run_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def background_monitoring(self):
        """
        Bluetooth 心拍監視 (Heartbeat) と背景スキャン。
        """
        while True:
            if self.engine.state != SystemState.UNLOCKED:
                # Bluetooth スキャンの実行
                await self.bt.scan_nearby_devices()
                await self.engine.update_auth_factor("BT_NEARBY", self.bt.is_nearby())

                # 顔認証の試行 (UIを介さずバックグラウンドで照合)
                # match, dist = self.face.authenticate()
                # await self.engine.update_auth_factor("FACE", match)

            # 設定された間隔（1〜60分）で監視
            interval = ConfigManager.get("heartbeat_interval_mins") or 10
            await asyncio.sleep(interval * 60)

    def on_auth_success(self, route):
        logger.info(f"AUTHORIZED: Access granted via {route}")
        self.os_ctrl.set_lock_mode(False)
        self.kb_hook.stop()

        # 監査ログの記録 (実際の顔写真をキャプチャ)
        self.audit.log_entry(route)

        # engineの状態を更新
        asyncio.run_coroutine_threadsafe(self.engine.unlock_system(route), self.loop)

    def start_wizard(self):
        """初回セットアップウィザードを起動。"""
        wizard = SetupWizard(self.root, on_complete=self.launch_lock_screen)
        wizard.grab_set()

    def launch_lock_screen(self):
        """ロック画面を表示。"""
        self.lock_screen = ShinobiLockScreen(self.root, on_auth_success=self.on_auth_success)

    def run(self):
        logger.info("SHINOBI_CORE System v3.1 Starting...")

        # 1. 権限とBitLocker確認
        if not is_admin():
            logger.warning("ELEVATED PRIVILEGES REQUIRED for full security features.")
        self.os_ctrl.check_bitlocker_status()

        # 2. フックと制限開始
        self.kb_hook.start()
        self.os_ctrl.set_lock_mode(True)

        # 3. 非同期ループ開始
        self.async_thread.start()
        asyncio.run_coroutine_threadsafe(self.background_monitoring(), self.loop)

        # 4. メインUI (Tkinter) 起動
        self.root = ctk.CTk()

        # 初回起動チェック
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
