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
    MFAエンジン (v3.4)
    スマホ鍵による単体解錠をサポート。
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
        解錠条件の判定。
        """
        # 特例: スマホ鍵 (BROWSER_KEY) がクリアされていれば、モードに関わらず即解錠。
        if self.auth_status["BROWSER_KEY"]:
            return True, "Mobile Key (Priority)"

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

        return False, f"Waiting for Authentication ({count}/2 cleared)"

    def record_pin_failure(self):
        self.pin_fail_count += 1
        if self.pin_fail_count >= 3:
            penalty = (self.pin_fail_count - 2) * 30
            self.lockout_until = time.time() + penalty
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
        self.pin_fail_count = 0
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
        from config_manager import ConfigManager
        while True:
            interval = (ConfigManager.get("heartbeat_interval_mins") or 10) * 60
            await asyncio.sleep(interval)
            if self.state == SystemState.LOCKED_MITIGATED:
                if not self.auth_status["BT_NEARBY"]:
                    self.state = SystemState.LOCKED_STRICT
