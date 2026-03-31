import asyncio
import sys
import os
import threading

# 自作モジュールのインポート
from mfa_engine import MFAEngine, SystemState
from bt_monitor import BluetoothMonitor
from face_auth import FaceAuth
from browser_key import BrowserKeyReceiver
from os_control import OSRegistryController
from ui import ShinobiLockScreen, AdminDashboard
from audit_watchdog import AuditLog

class ShinobiSystem:
    """
    究極セキュリティシステム「SHINOBI」のメイン統合クラス。
    """
    def __init__(self):
        self.engine = MFAEngine()
        self.bt = BluetoothMonitor()
        self.face = FaceAuth()
        self.browser_key = BrowserKeyReceiver()
        self.os_ctrl = OSRegistryController()
        self.audit = AuditLog()

        # モックフラグ（開発用）
        self.is_mock = True

    async def start(self):
        print("--- SHINOBI SYSTEM STARTUP ---")
        # 1. 初期ロックの実施 (Registry + Shell)
        self.os_ctrl.set_lock_mode(True)
        # self.os_ctrl.switch_to_custom_shell(sys.executable)

        # 2. 認証ループの開始 (バックグラウンドタスク)
        asyncio.create_task(self.engine.heartbeat_check())

        # 3. メイン認証フローのシミュレーション
        while True:
            if self.engine.state != SystemState.UNLOCKED:
                print(f"--- SYSTEM {self.engine.state.value} ---")

                # BTスキャンの実施
                await self.bt.scan_nearby_devices()
                await self.engine.update_auth_factor("BT_NEARBY", self.bt.is_nearby())

                # 顔認証の実施 (UIから呼び出す想定)
                # success, dist = self.face.capture_and_authenticate(mock_result=True)
                # await self.engine.update_auth_factor("FACE", success)

                # デモ用: PIN入力を待つ（擬似的に10秒ごとにチェック）
                await asyncio.sleep(10)
            else:
                # 解錠中の場合
                # ユーザーが「ロック」を選択するか、BT監視で離脱を検知するまで待機
                await asyncio.sleep(60)

    def run_lock_screen(self):
        """
        ロック画面 UI を別スレッドで起動。
        """
        import tkinter as tk
        root = tk.Tk()
        lock_screen = ShinobiLockScreen(root)
        root.mainloop()

if __name__ == "__main__":
    shinobi = ShinobiSystem()
    # 統合テスト実行 (非同期イベントループの開始)
    try:
        asyncio.run(shinobi.start())
    except KeyboardInterrupt:
        print("SHINOBI SHUTDOWN.")
