import asyncio
import uuid
import time
import logging
from config_manager import ConfigManager

logger = logging.getLogger("SHINOBI.BrowserKey")

class BrowserKeyReceiver:
    """
    スマホのブラウザから送信されたトークンを受信し、MFAエンジンへ通知する。
    """
    def __init__(self, service_uuid=None):
        self.service_uuid = service_uuid or "12345678-1234-5678-1234-567812345678"
        self.characteristic_uuid = "87654321-4321-8765-4321-876543210987"
        self.auth_success = False

    async def start_advertising(self, on_verified_callback):
        """
        PC側でGATTサーバーを稼働させ、スマホからの書き込みを待機。
        """
        logger.info(f"BLE_SERVER ONLINE: {self.service_uuid}")
        self.on_verified_callback = on_verified_callback

        # 実際にはここに BleakGATTServer の稼働ループが入る
        # self.server = BleakGATTServerWinRT(...)
        # await self.server.start()

    def on_token_received(self, handle, data):
        """
        スマホからデータが届いた時の処理。
        """
        try:
            received_token = data.decode('utf-8')
            logger.info(f"Received Token from Mobile: {received_token}")

            # 保存されている現在のトークンと比較
            stored_token = ConfigManager.get("browser_token")

            if received_token == stored_token:
                logger.info("Mobile Key Verification: SUCCESS")
                self.auth_success = True
                if self.on_verified_callback:
                    self.on_verified_callback(True)
                return True
            else:
                logger.warning("Mobile Key Verification: FAILED (Token Mismatch)")
                self.auth_success = False
                return False
        except Exception as e:
            logger.error(f"Error processing BLE data: {e}")
            return False

    async def simulate_receive(self, token):
        """テスト用モック"""
        logger.info(f"[SIMULATION] Mobile sending token: {token}")
        return self.on_token_received(None, token.encode('utf-8'))
