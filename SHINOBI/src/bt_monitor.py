import asyncio
from bleak import BleakScanner
import logging
from config_manager import ConfigManager

logger = logging.getLogger("SHINOBI.BT")

class BluetoothMonitor:
    """
    Bluetooth RSSI 監視 v4.0。
    実際のハードウェアによるリアルタイム近接検知。
    """
    def __init__(self):
        self.target_mac = ConfigManager.get("target_mac")
        self.rssi_threshold = ConfigManager.get("rssi_threshold") or -70
        self.current_rssi = -120

    async def scan_nearby_devices(self, timeout=5.0):
        """周囲のBluetoothデバイスをスキャン。"""
        if not self.target_mac: return False
        try:
            # 実際のハードウェア・スキャン
            devices = await BleakScanner.discover(timeout=timeout)
            found = False
            for d in devices:
                if d.address.upper() == self.target_mac.upper():
                    self.current_rssi = d.rssi
                    found = True
                    logger.info(f"Proximity Match: {d.address} RSSI: {d.rssi}dBm")
                    break
            if not found: self.current_rssi = -120
            return self.is_nearby()
        except Exception as e:
            logger.error(f"Hardware BT Scan Failed: {e}")
            return False

    def is_nearby(self):
        return self.current_rssi > self.rssi_threshold

    def update_settings(self):
        self.target_mac = ConfigManager.get("target_mac")
        self.rssi_threshold = ConfigManager.get("rssi_threshold")
