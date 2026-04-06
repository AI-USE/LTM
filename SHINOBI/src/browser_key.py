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
        GATTサーバーを稼働させ、外部からの書き込みを待機。
        """
        self.on_verified_callback = on_verified_callback
        logger.info(f"スマホ鍵待機中 (UUID: {self.service_uuid})")

        # BLEAK-GATT-SERVER 相当のロジック (概念的実装)
        # Windows API (WinRT) を直接叩く必要があるため、
        # 実際には bleak_gatt_server ライブラリ等の外部導入が必要。
        # ここでは、受信イベントを待ち受けるための非同期ループとして確立。
        while not self.auth_success:
            await asyncio.sleep(1)

    def on_token_received(self, handle, data):
        """
        スマホ側からのGATT Writeイベント受信時のコアロジック。
        """
        try:
            token = data.decode('utf-8')
            stored_token = ConfigManager.get("browser_token")

            if token == stored_token:
                logger.info("スマホ鍵の認証に成功しました。")
                self.auth_success = True
                if self.on_verified_callback:
                    self.on_verified_callback(True)
                return True
            else:
                logger.warning(f"不正なトークン入力を検知: {token}")
                return False
        except Exception as e:
            logger.error(f"GATTデータの解析中にエラー: {e}")
            return False

    async def simulate_receive(self, token):
        """テストおよび統合検証用"""
        return self.on_token_received(None, token.encode('utf-8'))
