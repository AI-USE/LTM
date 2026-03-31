import asyncio
import sys
import os
import logging
import threading
import tkinter as tk

# src ディレクトリを sys.path に追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'SHINOBI/src'))

from mfa_engine import MFAEngine, SystemState
from bt_monitor import BluetoothMonitor
from face_auth import FaceAuth
from browser_key import BrowserKeyReceiver
from os_control import OSRegistryController, is_admin
from ui import ShinobiLockScreen, AdminDashboard
from audit_watchdog import AuditLog, Watchdog
from keyboard_hook import KeyboardHook
from config_manager import ConfigManager

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
        self.watchdog = Watchdog()

        self.root = None
        self.lock_screen = None
        self.loop = asyncio.new_event_loop()
        self.async_thread = threading.Thread(target=self.run_async_loop, daemon=True)

    def run_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def background_monitoring(self):
        """
        BT監視、顔認証のトリガー、ハートビート等をバックグラウンドで実行。
        """
        while True:
            if self.engine.state != SystemState.UNLOCKED:
                # BTスキャン
                await self.bt.scan_nearby_devices()
                await self.engine.update_auth_factor("BT_NEARBY", self.bt.is_nearby())

                # 顔認証の試行 (UIスレッドへの通知はイベント等で行う)
                # success, dist = self.face.capture_and_authenticate()
                # await self.engine.update_auth_factor("FACE", success)

            await asyncio.sleep(10) # 10秒ごとに監視

    def on_auth_success(self, route):
        logger.info(f"Authentication Success via {route}")
        # UIから呼ばれる。OSの制限を解除し、explorerを起動
        self.os_ctrl.set_lock_mode(False)
        self.kb_hook.stop()
        self.audit.log_entry(route)
        # engineの状態を更新
        asyncio.run_coroutine_threadsafe(self.engine.unlock_system(route), self.loop)

    def run(self):
        logger.info("SHINOBI System Starting...")

        # 1. 権限チェック
        if not is_admin():
            logger.warning("Running without Admin privileges. Some features (Registry/Shell) will be disabled.")

        # 2. キーボードフック開始
        self.kb_hook.start()

        # 3. レジストリ制限の有効化
        self.os_ctrl.set_lock_mode(True)

        # 4. 非同期ループスレッド開始
        self.async_thread.start()
        asyncio.run_coroutine_threadsafe(self.background_monitoring(), self.loop)
        asyncio.run_coroutine_threadsafe(self.engine.heartbeat_check(), self.loop)

        # 5. Tkinter メインループ (ロック画面)
        self.root = tk.Tk()
        self.lock_screen = ShinobiLockScreen(self.root, on_auth_success=self.on_auth_success)

        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.kb_hook.stop()
            self.os_ctrl.set_lock_mode(False)

if __name__ == "__main__":
    app = ShinobiApp()
    app.run()
