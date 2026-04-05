import asyncio
from bleak import BleakScanner
import logging

logger = logging.getLogger("SHINOBI.BT")

class BluetoothMonitor:
    """
    Bluetooth RSSI 監視。
    実際のハードウェアスキャンを実装。
    """
    def __init__(self, target_mac=None, rssi_threshold=-70):
        self.target_mac = target_mac
        self.rssi_threshold = rssi_threshold
        self.current_rssi = -120

    async def scan_nearby_devices(self):
        """周囲のデバイスを5秒間スキャン。"""
        if not self.target_mac:
            return False

        try:
            # 5秒間のスキャン
            devices = await BleakScanner.discover(timeout=5.0)
            found = False
            for d in devices:
                if d.address.upper() == self.target_mac.upper():
                    self.current_rssi = d.rssi
                    found = True
                    logger.info(f"Target BT Found: {d.name or 'Unknown'} ({d.address}) RSSI: {d.rssi}dBm")
                    break

            if not found:
                self.current_rssi = -120
                logger.debug("Target BT not in range.")

            return self.is_nearby()
        except Exception as e:
            logger.error(f"Bluetooth scan error: {e}")
            self.current_rssi = -120
            return False

    def is_nearby(self):
        return self.current_rssi > self.rssi_threshold

    def set_threshold(self, val):
        self.rssi_threshold = val
