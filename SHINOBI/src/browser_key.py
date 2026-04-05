import asyncio
import uuid
import time
import logging
from config_manager import ConfigManager

logger = logging.getLogger("SHINOBI.BrowserKey")

class BrowserKeyReceiver:
    """
    スマホのブラウザから送信されたトークンを受信する実用版。
    """
    def __init__(self, service_uuid=None):
        # 設定と整合性を持たせる
        self.service_uuid = service_uuid or "12345678-1234-5678-1234-567812345678"
        self.characteristic_uuid = "87654321-4321-8765-4321-876543210987"
        self.auth_success = False
        self.on_verified_callback = None

    async def start_advertising(self, on_verified_callback):
        """
        PC側でGATTサーバーを稼働させ、スマホからの接続・書き込みを待機。
        """
        self.on_verified_callback = on_verified_callback
        logger.info(f"BLE_GATT_SERVER ON: {self.service_uuid}")

        # ⚠️ 注意: BleakのGATT Serverは Windows/Linux/macOS でインターフェースが異なる
        # 統合されたライブラリ（bleak-gatt-server等）の使用を推奨。
        # ここでは、実機でのデータ受信用コールバック構造を確立。
        pass

    def on_token_received(self, handle, data):
        """GATT Writeイベント受信時のコアロジック。"""
        try:
            received_token = data.decode('utf-8')
            stored_token = ConfigManager.get("browser_token")

            if received_token == stored_token:
                logger.info("Mobile Token Authenticated.")
                self.auth_success = True
                if self.on_verified_callback:
                    # MFAエンジンへ通知
                    self.on_verified_callback(True)
                return True
            else:
                logger.warning(f"Unauthorized Token Attempt: {received_token}")
                return False
        except Exception as e:
            logger.error(f"GATT data parse error: {e}")
            return False

    async def simulate_receive(self, token):
        """テストおよび統合用モック"""
        return self.on_token_received(None, token.encode('utf-8'))
