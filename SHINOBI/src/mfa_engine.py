import asyncio
import time
from enum import Enum

# 先ほど作成した各モジュールをインポート（実際にはパスを通すか、同一ディレクトリに配置）
# from bt_monitor import BluetoothMonitor
# from face_auth import FaceAuth
# from browser_key import BrowserKeyReceiver
# from os_control import OSRegistryController

class SystemState(Enum):
    LOCKED_STRICT = "STRICT"      # 厳格モード（2FA以上必要）
    LOCKED_MITIGATED = "MITIGATED" # 緩和モード（1要素で解除可能）
    UNLOCKED = "UNLOCKED"         # 解錠中（explorer.exe 稼働中）

class MFAEngine:
    """
    SHINOBIの全認証ロジックを統合し、状態を管理するコアエンジン。
    """
    def __init__(self):
        self.state = SystemState.LOCKED_STRICT
        self.last_unlock_time = 0
        self.mitigation_window = 3600  # 1時間 (3600秒)
        self.heartbeat_interval = 600   # 10分 (600秒)

        # 認証要素の状態（擬似的なもの。実際には各モジュールから取得）
        self.auth_status = {
            "FACE": False,
            "BT_NEARBY": False,
            "PIN": False,
            "BROWSER_KEY": False
        }

    def check_unlock_conditions(self):
        """
        現在の認証要素から解錠可能か判定する。
        """
        # --- 2.1 厳格モード（通常時・起動時）の判定 ---
        if self.state == SystemState.LOCKED_STRICT:
            # ステルス: 顔認証 ＋ スマホBT接近
            if self.auth_status["FACE"] and self.auth_status["BT_NEARBY"]:
                return True, "Stealth (Face + BT)"

            # ハイブリッド: PIN ＋ スマホBT接近
            if self.auth_status["PIN"] and self.auth_status["BT_NEARBY"]:
                return True, "Hybrid (PIN + BT)"

            # ブラウザ鍵: スマホ指紋済トークン
            if self.auth_status["BROWSER_KEY"]:
                return True, "Browser Key"

            # W認証: 顔認証 ＋ PIN（スマホなし時）
            if self.auth_status["FACE"] and self.auth_status["PIN"]:
                return True, "W-Auth (Face + PIN)"

            # 救済登録: PINのみ (特別なログが必要)
            # ※本来は「顔が検知・記録されるまでボタン無効」だが、
            # 認証ロジックとしては、ここで「救済ルート」として扱う。
            if self.auth_status["PIN"] and not self.auth_status["BT_NEARBY"] and not self.auth_status["FACE"]:
                return True, "Recovery Route (PIN Only)"

        # --- 2.2 スマート緩和プロトコル（利便性）の判定 ---
        elif self.state == SystemState.LOCKED_MITIGATED:
            # 1要素（顔 or BT or PIN）のみで即解錠
            if any([self.auth_status["FACE"], self.auth_status["BT_NEARBY"], self.auth_status["PIN"]]):
                return True, "Mitigated (1-Factor)"

        return False, "Not enough factors"

    async def update_auth_factor(self, factor_name, value):
        """
        認証要素（顔、BT、PIN、ブラウザ鍵等）が更新された際に呼び出す。
        """
        self.auth_status[factor_name] = value

        # 解錠判定
        if self.state != SystemState.UNLOCKED:
            can_unlock, route = self.check_unlock_conditions()
            if can_unlock:
                await self.unlock_system(route)

    async def unlock_system(self, route):
        print(f"--- SYSTEM UNLOCKED via {route} ---")
        self.state = SystemState.UNLOCKED
        self.last_unlock_time = time.time()
        # ここで explorer.exe 起動 & レジストリ復元を行う (OSControl)
        print("Explorer started. Registry restrictions removed.")

    async def lock_system(self):
        """
        システムをロックし、現在の状況に応じてモードを決定。
        """
        now = time.time()
        # 1時間以内の解除履歴があるか判定
        if (now - self.last_unlock_time) < self.mitigation_window:
            self.state = SystemState.LOCKED_MITIGATED
            print("--- SYSTEM LOCKED (Mitigated Mode) ---")
        else:
            self.state = SystemState.LOCKED_STRICT
            print("--- SYSTEM LOCKED (Strict Mode) ---")

        # 各要素をリセット
        for key in self.auth_status:
            self.auth_status[key] = False

        # ここで explorer.exe 終了 & レジストリ制限を有効化

    async def heartbeat_check(self):
        """
        10分おきのBT生存確認。
        """
        while True:
            await asyncio.sleep(self.heartbeat_interval)
            if self.state == SystemState.LOCKED_MITIGATED:
                # BTが離れていないか確認 (BT_NEARBYを再評価)
                # ここでは擬似的に確認
                is_bt_away = not self.auth_status["BT_NEARBY"]
                if is_bt_away:
                    print("Heartbeat: BT lost. Escalating to STRICT mode.")
                    self.state = SystemState.LOCKED_STRICT

async def test_mfa():
    engine = MFAEngine()

    # 1. 最初は厳格モードでロックされている
    print(f"Current State: {engine.state}")

    # 2. 顔認証だけでは解錠されない（厳格モード）
    print("\n[Step 2] Face detected...")
    await engine.update_auth_factor("FACE", True)
    print(f"State: {engine.state}")

    # 3. スマホが接近すると解錠（ステルスルート）
    print("\n[Step 3] BT nearby detected...")
    await engine.update_auth_factor("BT_NEARBY", True)
    print(f"State: {engine.state}")

    # 4. ロックする（1時間以内なので緩和モードへ）
    print("\n[Step 4] Locking system...")
    await engine.lock_system()
    print(f"State: {engine.state}")

    # 5. 緩和モードでは1要素（PINだけ）で解錠
    print("\n[Step 5] PIN entered in Mitigated mode...")
    await engine.update_auth_factor("PIN", True)
    print(f"State: {engine.state}")

if __name__ == "__main__":
    asyncio.run(test_mfa())
