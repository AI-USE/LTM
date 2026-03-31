import asyncio
import platform
import random

try:
    from bleak import BleakScanner
    BLEAK_AVAILABLE = True
except ImportError:
    BLEAK_AVAILABLE = False

class BluetoothMonitor:
    """
    Bluetooth RSSI (電波強度) を監視し、デバイスとの距離を判定するクラス。
    """
    def __init__(self, target_mac=None, rssi_threshold=-70, mock=False):
        self.target_mac = target_mac
        self.rssi_threshold = rssi_threshold
        self.current_rssi = -120
        self.mock = mock

    async def scan_nearby_devices(self):
        """
        周囲のデバイスをスキャンし、ターゲットのRSSIを取得する。
        """
        if self.mock:
            # デモ・テスト用のモック動作
            self.current_rssi = random.randint(-90, -40)
            print(f"[MOCK] Scanning... Found Target. RSSI: {self.current_rssi} dBm")
            return self.is_nearby()

        if not BLEAK_AVAILABLE:
            print("Bleak library is not available. Please install it with 'pip install bleak'.")
            return False

        try:
            devices = await BleakScanner.discover(timeout=5.0)
            found = False
            for d in devices:
                if self.target_mac and d.address.upper() == self.target_mac.upper():
                    # metadataからRSSIを取得 (Bleakのバージョンにより異なる場合がある)
                    self.current_rssi = d.rssi
                    found = True
                    print(f"Found Target: {d.name} ({d.address}) RSSI: {d.rssi} dBm")
                    break

            if not found:
                self.current_rssi = -120
                print(f"Target device {self.target_mac} not found.")

        except Exception as e:
            print(f"Bluetooth Scan Error: {e}")
            self.current_rssi = -120

        return self.is_nearby()

    def is_nearby(self):
        """
        現在のRSSIが閾値を超えているか（近くにいるか）を判定。
        """
        return self.current_rssi > self.rssi_threshold

    def set_threshold(self, value):
        self.rssi_threshold = value

async def test_bluetooth():
    # 環境に応じてモックモードを切り替え
    is_mock = (platform.system() != "Windows")
    monitor = BluetoothMonitor(target_mac="00:11:22:33:44:55", rssi_threshold=-70, mock=is_mock)

    for i in range(3):
        print(f"\n--- Scan Attempt {i+1} ---")
        nearby = await monitor.scan_nearby_devices()
        status = "NEAR (PASS)" if nearby else "FAR (FAIL)"
        print(f"Status: {status} (Current RSSI: {monitor.current_rssi} dBm, Threshold: {monitor.rssi_threshold} dBm)")
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(test_bluetooth())
