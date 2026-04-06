import asyncio
from bleak import BleakScanner, BleakClient
import logging
from config_manager import ConfigManager

logger = logging.getLogger("SHINOBI.BT")

class BluetoothMonitor:
    """
    Bluetooth RSSI 監視 v4.1 (完全ハードウェア対応版)。
    """
    def __init__(self, target_mac=None):
        self.target_mac = target_mac or ConfigManager.get("target_mac")
        self.rssi_threshold = ConfigManager.get("rssi_threshold") or -70
        self.current_rssi = -120

    async def scan_nearby_devices(self, timeout=5.0):
        """
        BleakScannerを使用して、実際に周囲のデバイスを探索する。
        """
        if not self.target_mac:
            return False

        try:
            # 実際のBluetoothハードウェアを使用
            devices = await BleakScanner.discover(timeout=timeout)

            found = False
            for d in devices:
                if d.address.upper() == self.target_mac.upper():
                    self.current_rssi = d.rssi
                    found = True
                    logger.info(f"Target Identity Verified: {d.name or 'N/A'} [{d.address}] Signal: {d.rssi}dBm")
                    break

            if not found:
                self.current_rssi = -120

            return self.is_nearby()

        except Exception as e:
            logger.error(f"Bluetooth Hardware Error: {e}")
            self.current_rssi = -120
            return False

    def is_nearby(self):
        return self.current_rssi > self.rssi_threshold

    def refresh_target(self):
        self.target_mac = ConfigManager.get("target_mac")
        self.rssi_threshold = ConfigManager.get("rssi_threshold") or -70
