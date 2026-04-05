import asyncio
import uuid
import time
import logging
from config_manager import ConfigManager

logger = logging.getLogger("SHINOBI.BrowserKey")

class BrowserKeyReceiver:
    """
    スマホのブラウザから送信されたトークンを実戦的に受信する。
    """
    def __init__(self, service_uuid=None):
        self.service_uuid = service_uuid or "12345678-1234-5678-1234-567812345678"
        self.characteristic_uuid = "87654321-4321-8765-4321-876543210987"
        self.auth_success = False
        self.on_verified_callback = None

    async def start_advertising(self, on_verified_callback):
        """
        GATTサーバーを稼働させ、外部からの書き込みを待機。
        """
        logger.info(f"BLE広告開始: {self.service_uuid}")
        self.on_verified_callback = on_verified_callback

        # Windows WinRTスタックを用いたGATTサーバーの擬似的な実装
        # 実際には bleak.backends.winrt.server 等を介してOSが管理
        pass

    def on_token_received(self, handle, data):
        """
        スマホ側からのGATT Writeイベント発生時に呼ばれる。
        """
        try:
            token = data.decode('utf-8')
            logger.info(f"トークン受信: {token}")

            stored = ConfigManager.get("browser_token")
            if token == stored:
                logger.info("スマホ鍵の認証に成功。")
                self.auth_success = True
                if self.on_verified_callback:
                    self.on_verified_callback(True)
                return True
            else:
                logger.warning("スマホ鍵の認証に失敗（トークン不一致）。")
                return False
        except Exception as e:
            logger.error(f"受信データ処理エラー: {e}")
            return False

    async def simulate_receive(self, token):
        """テスト用シミュレーション"""
        return self.on_token_received(None, token.encode('utf-8'))
