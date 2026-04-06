import asyncio
import sys
import os
import logging
import threading
import subprocess
import customtkinter as ctk

# パス解決: SHINOBI/src 自身をパスに追加し、siblings を名前のみで import 可能にする
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# 親ディレクトリ(SHINOBI)もパスに追加（パッケージとしての import 用）
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

try:
    import config_manager
    import mfa_engine
    import bt_monitor
    import face_auth
    import browser_key
    import os_control
    import ui
    import audit_watchdog
    import keyboard_hook
    import setup_wizard
except ImportError:
    # パッケージとしてのインポート (ROOT から main.py を叩いた場合)
    from . import config_manager
    from . import mfa_engine
    from . import bt_monitor
    from . import face_auth
    from . import browser_key
    from . import os_control
    from . import ui
    from . import audit_watchdog
    from . import keyboard_hook
    from . import setup_wizard

ConfigManager = config_manager.ConfigManager
MFAEngine = mfa_engine.MFAEngine
SystemState = mfa_engine.SystemState
BluetoothMonitor = bt_monitor.BluetoothMonitor
FaceAuth = face_auth.FaceAuth
BrowserKeyReceiver = browser_key.BrowserKeyReceiver
OSRegistryController = os_control.OSRegistryController
is_admin = os_control.is_admin
ShinobiLockScreen = ui.ShinobiLockScreen
AdminDashboard = ui.AdminDashboard
AuditLog = audit_watchdog.AuditLog
KeyboardHook = keyboard_hook.KeyboardHook
SetupWizard = setup_wizard.SetupWizard

ConfigManager.initialize()

# ロギング
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] SHINOBI: %(message)s')
logger = logging.getLogger("SHINOBI.Core")

class ShinobiApp:
    def __init__(self):
        self.engine = MFAEngine()
        self.bt = BluetoothMonitor()
        self.face = FaceAuth()
        self.browser_key = BrowserKeyReceiver()
        self.os_ctrl = OSRegistryController()
        self.audit = AuditLog()
        self.kb_hook = KeyboardHook()

        self.last_face_dist = 1.0
        self.root = None
        self.loop = asyncio.new_event_loop()
        self.async_thread = threading.Thread(target=self.run_async_loop, daemon=True)

    def run_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def ensure_watchdog(self):
        """
        監視プロセス (Guard) が動いているか確認し、無ければ起動。
        """
        if getattr(sys, 'frozen', False):
            # EXE化されている場合
            guard_path = os.path.join(os.path.dirname(sys.executable), "SHINOBI_GUARD_v4.exe")
            if os.path.exists(guard_path):
                logger.info("Double-Guard 監視プロセスを確認中...")
                # 簡易的な起動（多重起動防止は Guard 側で行う）
                subprocess.Popen([guard_path, sys.executable], creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)

    async def background_monitoring(self):
        while True:
            if self.engine.state != SystemState.UNLOCKED:
                await self.bt.scan_nearby_devices()
                asyncio.run_coroutine_threadsafe(self.engine.update_auth_factor("BT_NEARBY", self.bt.is_nearby()), self.loop)
                self.face.authenticate_async(self.on_face_result)
            await asyncio.sleep(5)

    def on_face_result(self, m, d):
        self.last_face_dist = d
        if self.engine.state != SystemState.UNLOCKED:
            asyncio.run_coroutine_threadsafe(self.engine.update_auth_factor("FACE", m), self.loop)

    def on_token_verified(self, success):
        if success and self.engine.state != SystemState.UNLOCKED:
            asyncio.run_coroutine_threadsafe(self.engine.update_auth_factor("BROWSER_KEY", True), self.loop)

    def on_auth_success(self, route):
        logger.info(f"AUTHORIZED: {route}")
        self.os_ctrl.set_lock_mode(False)
        self.kb_hook.stop()
        self.audit.log_entry(route)
        asyncio.run_coroutine_threadsafe(self.engine.unlock_system(route), self.loop)

    def launch_lock_screen(self):
        ShinobiLockScreen(self.root, self.engine, on_auth_success=self.on_auth_success)

    def run(self):
        logger.info("SHINOBI v4.2 起動準備完了。")
        self.ensure_watchdog() # 監視プロセスの起動
        self.os_ctrl.check_bitlocker_status()
        self.kb_hook.start()
        self.os_ctrl.set_lock_mode(True)

        self.async_thread.start()
        asyncio.run_coroutine_threadsafe(self.background_monitoring(), self.loop)
        asyncio.run_coroutine_threadsafe(self.engine.heartbeat_check(), self.loop)
        asyncio.run_coroutine_threadsafe(self.browser_key.start_advertising(self.on_token_verified), self.loop)

        self.root = ctk.CTk()
        if not ConfigManager.get("setup_complete"):
            wizard = SetupWizard(self.root, on_complete=self.launch_lock_screen)
            wizard.grab_set()
        else:
            self.launch_lock_screen()

        try:
            self.root.mainloop()
        finally:
            self.kb_hook.stop()
            self.os_ctrl.set_lock_mode(False)

if __name__ == "__main__":
    ShinobiApp().run()
