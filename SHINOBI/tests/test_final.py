import asyncio
import sys
import os
import logging

# src ディレクトリを sys.path に追加
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from mfa_engine import MFAEngine, SystemState
from bt_monitor import BluetoothMonitor
from face_auth import FaceAuth
from os_control import OSRegistryController
from audit_watchdog import AuditLog
from config_manager import ConfigManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SHINOBI.Test")

async def final_integration_test():
    logger.info("--- SHINOBI FINAL INTEGRATED TEST START ---")

    # 1. コンポーネント初期化
    ConfigManager.initialize()
    engine = MFAEngine()
    bt = BluetoothMonitor(target_mac="11:22:33:44:55:66", rssi_threshold=-100, mock=True)
    face = FaceAuth()
    os_ctrl = OSRegistryController()
    audit = AuditLog()

    # 2. 初期状態確認
    logger.info(f"Initial State: {engine.state}")
    os_ctrl.set_lock_mode(True)

    # 3. 認証テスト (PIN検証)
    test_pin = "0000" # デフォルト
    if ConfigManager.verify_pin(test_pin):
        logger.info(f"PIN Verification SUCCESS: {test_pin}")
        await engine.update_auth_factor("PIN", True)
    else:
        logger.error(f"PIN Verification FAILED: {test_pin}")

    # 4. 認証テスト (BT接近)
    await bt.scan_nearby_devices()
    await engine.update_auth_factor("BT_NEARBY", bt.is_nearby())

    # 5. 解錠確認
    logger.info(f"Final State: {engine.state}")
    if engine.state == SystemState.UNLOCKED:
        os_ctrl.set_lock_mode(False)
        audit.log_entry("Hybrid (PIN+BT)")
        logger.info("Final Integration Test: UNLOCK SUCCESS.")
    else:
        logger.error("Final Integration Test: UNLOCK FAILED.")

    # 6. クリーンアップ (テスト後に制限を解除)
    os_ctrl.set_lock_mode(False)
    logger.info("--- SHINOBI FINAL INTEGRATED TEST COMPLETED ---")

if __name__ == "__main__":
    asyncio.run(final_integration_test())
