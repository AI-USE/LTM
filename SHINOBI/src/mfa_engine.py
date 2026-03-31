import asyncio
import time
from enum import Enum
import logging

logger = logging.getLogger("SHINOBI.MFA")

class SystemState(Enum):
    LOCKED_STRICT = "STRICT"
    LOCKED_MITIGATED = "MITIGATED"
    UNLOCKED = "UNLOCKED"

class MFAEngine:
    """
    刷新されたMFAエンジン。
    任意の2要素クリアでの解錠、およびPIN失敗ペナルティを実装。
    """
    def __init__(self):
        self.state = SystemState.LOCKED_STRICT
        self.last_unlock_time = 0

        # 各要素のクリア状態
        self.auth_status = {
            "FACE": False,
            "BT_NEARBY": False,
            "PIN": False,
            "BROWSER_KEY": False
        }

        # PIN失敗管理
        self.pin_fail_count = 0
        self.lockout_until = 0

    def check_unlock_conditions(self):
        """
        任意の2要素がクリアされているか判定。
        """
        cleared_factors = [k for k, v in self.auth_status.items() if v]
        count = len(cleared_factors)

        # 緩和モード: 1要素でOK
        if self.state == SystemState.LOCKED_MITIGATED:
            if count >= 1:
                return True, f"Mitigated (Factor: {cleared_factors[0]})"

        # 厳格モード: 2要素以上でOK
        elif self.state == SystemState.LOCKED_STRICT:
            if count >= 2:
                return True, f"Multi-Factor ({'+'.join(cleared_factors)})"

        return False, f"Need more factors ({count}/2 cleared)"

    def record_pin_failure(self):
        """
        PIN失敗時にペナルティ時間を計算。
        """
        self.pin_fail_count += 1
        # 3回目から段階的にロック
        if self.pin_fail_count >= 3:
            penalty = (self.pin_fail_count - 2) * 30 # 30s, 60s, 90s...
            self.lockout_until = time.time() + penalty
            logger.warning(f"PIN Lockout active for {penalty}s")
            return penalty
        return 0

    def is_pin_locked(self):
        return time.time() < self.lockout_until

    def get_lockout_remaining(self):
        return max(0, int(self.lockout_until - time.time()))

    async def update_auth_factor(self, factor_name, value):
        self.auth_status[factor_name] = value

    def reset_auth_factors(self):
        for k in self.auth_status: self.auth_status[k] = False

    async def unlock_system(self, route):
        self.state = SystemState.UNLOCKED
        self.last_unlock_time = time.time()
        self.pin_fail_count = 0 # 成功時はリセット
        logger.info(f"System Unlocked via {route}")

    async def lock_system(self, manual=False):
        now = time.time()
        from config_manager import ConfigManager
        window = (ConfigManager.get("smart_mitigation_hours") or 1) * 3600

        if not manual and (now - self.last_unlock_time) < window:
            self.state = SystemState.LOCKED_MITIGATED
        else:
            self.state = SystemState.LOCKED_STRICT

        self.reset_auth_factors()
        logger.info(f"System Locked. State: {self.state}")

    async def heartbeat_check(self):
        """10分おきのBT生存確認。"""
        from config_manager import ConfigManager
        while True:
            interval = (ConfigManager.get("heartbeat_interval_mins") or 10) * 60
            await asyncio.sleep(interval)

            if self.state == SystemState.LOCKED_MITIGATED:
                # BTが離れていれば強制的に厳格モードへ
                if not self.auth_status["BT_NEARBY"]:
                    logger.info("Heartbeat: BT lost. Escalating to STRICT.")
                    self.state = SystemState.LOCKED_STRICT
