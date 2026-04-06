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

async def test_mobile_key_priority():
    logger.info("--- SHINOBI v3.4 MOBILE KEY PRIORITY TEST START ---")

    ConfigManager.initialize()
    engine = MFAEngine()

    # 1. 最初は厳格モード
    logger.info(f"Initial State: {engine.state}")

    # 2. スマホ鍵のみをクリア
    logger.info("Simulating Mobile Key Authentication...")
    await engine.update_auth_factor("BROWSER_KEY", True)

    # 3. 判定
    can_unlock, route = engine.check_unlock_conditions()
    if can_unlock and "Mobile Key" in route:
        await engine.unlock_system(route)
        logger.info(f"SUCCESS: System unlocked via single factor (Mobile Key). State: {engine.state}")
    else:
        logger.error(f"FAILURE: System did not unlock via single Mobile Key. Status: {route}")

    # 4. 別の要素（PIN）のみで試行（解錠されないはず）
    engine.reset_auth_factors()
    await engine.lock_system(manual=True)
    logger.info(f"Relocked State: {engine.state}")

    logger.info("Simulating PIN Only (should not unlock)...")
    await engine.update_auth_factor("PIN", True)
    can_unlock, route = engine.check_unlock_conditions()
    if not can_unlock:
        logger.info("SUCCESS: PIN only did not unlock (as expected).")
    else:
        logger.error(f"FAILURE: System unlocked with only 1 non-priority factor. Route: {route}")

    logger.info("--- SHINOBI v3.4 MOBILE KEY PRIORITY TEST COMPLETED ---")

if __name__ == "__main__":
    asyncio.run(test_mobile_key_priority())
