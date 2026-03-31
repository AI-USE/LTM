import asyncio
import uuid
import time

class BrowserKeyReceiver:
    """
    スマホのブラウザから送られてくるBluetooth経由のトークンを受信するクラス。
    """
    def __init__(self, service_uuid=None):
        # サービスUUIDを固定またはランダム生成
        self.service_uuid = service_uuid or str(uuid.uuid4())
        self.received_token = None
        self.auth_success = False

    async def start_advertising(self):
        """
        PC側でBluetoothのアドバタイズを開始し、スマホからの接続・書き込みを待機する。
        (BleakのGATTサーバー機能を利用する想定)
        """
        print(f"Starting BLE Advertising... (Service UUID: {self.service_uuid})")
        # 実際には bleak_gatt_server 等を使用する
        # ここではモックとして、スマホからの入力を模したループを回す
        print("Waiting for smartphone authentication signal...")

    def verify_token(self, token):
        """
        受信したトークンの検証。
        """
        # トークンはWebAuthn等で署名されたもの、あるいは共有の秘密鍵
        # 今回は簡易的に静的なキーと比較。
        secret_key = "SHINOBI_TOKEN_12345"
        if token == secret_key:
            print("Token verification SUCCESS.")
            self.auth_success = True
            return True
        else:
            print("Token verification FAILED.")
            self.auth_success = False
            return False

    async def simulate_receive(self, token):
        """
        テスト用: スマホからトークンが届いたことをシミュレートする。
        """
        print(f"[MOCK] Received Token from smartphone: {token}")
        self.received_token = token
        return self.verify_token(token)

async def test_browser_key():
    receiver = BrowserKeyReceiver(service_uuid="12345678-1234-5678-1234-567812345678")
    await receiver.start_advertising()

    # 正しいトークンをシミュレート
    print("\n--- Testing correct token ---")
    await receiver.simulate_receive("SHINOBI_TOKEN_12345")
    print(f"Is Auth Successful? {receiver.auth_success}")

    # 間違ったトークンをシミュレート
    print("\n--- Testing wrong token ---")
    await receiver.simulate_receive("WRONG_TOKEN")
    print(f"Is Auth Successful? {receiver.auth_success}")

if __name__ == "__main__":
    asyncio.run(test_browser_key())
