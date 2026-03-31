import asyncio
import sys
import os

# src ディレクトリを sys.path に追加してインポート可能にする
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from mfa_engine import MFAEngine, SystemState
from bt_monitor import BluetoothMonitor
from face_auth import FaceAuth
from os_control import OSRegistryController
from audit_watchdog import AuditLog

async def main_test():
    # 1. 各コンポーネントの初期化
    engine = MFAEngine()
    # 閾値を緩めて確実にパスさせる
    bt = BluetoothMonitor(target_mac="11:22:33:44:55:66", rssi_threshold=-100, mock=True)
    face = FaceAuth()
    os_ctrl = OSRegistryController()
    audit = AuditLog()

    print("\n--- SHINOBI INTEGRATED TEST START ---")

    # 2. 初期ロック (レジストリ)
    os_ctrl.set_lock_mode(True)

    # 3. 初期状態は STRICT モード
    print(f"Current State: {engine.state}")

    # 4. 認証: ステルスルート (Face + BT)
    # 顔認証成功をシミュレート
    print("\n[Step 4] Simulating Face Auth success...")
    success, dist = face.capture_and_authenticate(mock_result=True)
    await engine.update_auth_factor("FACE", success)

    # BTスキャンの実施
    print("[Step 4] Simulating BT Scan...")
    await bt.scan_nearby_devices()
    await engine.update_auth_factor("BT_NEARBY", bt.is_nearby())

    # 5. 解錠されたことを確認
    print(f"\nFinal State: {engine.state}")
    if engine.state == SystemState.UNLOCKED:
        os_ctrl.set_lock_mode(False) # 制限解除
        audit.log_entry("Stealth (Face+BT)")
        print("Integration Test: UNLOCK SUCCESS.")
    else:
        print("Integration Test: UNLOCK FAILED.")

    # 6. 再ロック (1時間以内なので MITIGATED へ)
    print("\n[Step 6] Relocking system (within 1 hour window)...")
    await engine.lock_system()
    os_ctrl.set_lock_mode(True)
    print(f"Post-lock State: {engine.state}")

    # 7. 緩和モードでの 1要素解錠テスト
    print("\n[Step 7] Simulating 1-factor unlock (PIN) in MITIGATED mode...")
    await engine.update_auth_factor("PIN", True)
    print(f"Final State (after PIN): {engine.state}")

    print("\n--- SHINOBI INTEGRATED TEST COMPLETED ---")

if __name__ == "__main__":
    asyncio.run(main_test())
