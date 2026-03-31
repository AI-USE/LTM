import asyncio
import uuid
import time
import logging
from config_manager import ConfigManager

logger = logging.getLogger("SHINOBI.BrowserKey")

class BrowserKeyReceiver:
    """
    スマホのブラウザ（Web Bluetooth API）から送信された認証トークンを受信する。
    """
    def __init__(self, service_uuid=None):
        # サービスUUIDを固定またはランダム生成
        self.service_uuid = service_uuid or "12345678-1234-5678-1234-567812345678"
        self.characteristic_uuid = "87654321-4321-8765-4321-876543210987"
        self.received_token = None
        self.auth_success = False

    async def start_advertising(self):
        """
        PC側でBluetoothのアドバタイズを開始し、スマホからの接続・書き込みを待機する。
        (BleakGATTServerを使用することを想定)
        """
        logger.info(f"BLE_SERVER ONLINE: Service={self.service_uuid}")

        # WindowsのWinRTスタックを使用したGATTサーバーの実装（雛形）
        # try:
        #     from bleak.backends.winrt.server import BleakGATTServerWinRT
        #     server = BleakGATTServerWinRT()
        #     # サービスの定義
        #     await server.add_new_service(self.service_uuid)
        #     await server.add_new_characteristic(self.service_uuid, self.characteristic_uuid, ["write"], None)
        #     # 書き込みイベントの購読
        #     server.set_characteristic_write_callback(self.characteristic_uuid, self.on_token_received)
        #     await server.start()
        # except ImportError:
        #     logger.warning("BLE Server not available on this platform.")

    def on_token_received(self, handle, data):
        """
        GATT書き込みイベント（スマホからの解錠指示）のコールバック。
        """
        try:
            token = data.decode('utf-8')
            logger.info(f"Received Token: {token}")
            self.received_token = token
            return self.verify_token(token)
        except Exception as e:
            logger.error(f"Failed to process token data: {e}")
            return False

    def verify_token(self, token):
        """
        トークンの検証ロジック。
        """
        # 実際には ConfigManager.get("browser_token_hash") と比較
        # 今回は簡易的に静的キーとの比較
        secret_key = "SHINOBI_TOKEN_12345"
        if token == secret_key:
            logger.info("Token Verification: SUCCESS")
            self.auth_success = True
            return True
        else:
            logger.warning("Token Verification: FAILED (Unauthorized Device)")
            self.auth_success = False
            return False

    async def simulate_receive(self, token):
        """
        テスト・デモ用モック。
        """
        logger.info(f"[SIMULATION] Received Token: {token}")
        return self.verify_token(token)
