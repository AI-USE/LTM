import os
import json
import hashlib
import logging

logger = logging.getLogger("SHINOBI.Config")

class ConfigManager:
    """
    SHINOBI 構成管理モジュール。
    設定の永続化、検証、自動バックアップを担当。
    """
    # カレントディレクトリ（実行ファイルのある場所）を基準にする
    BASE_DIR = os.getcwd()
    CONFIG_PATH = os.path.join(BASE_DIR, "SHINOBI", "assets", "config.json")
    BACKUP_PATH = os.path.join(BASE_DIR, "SHINOBI", "assets", "config_backup.json")

    @staticmethod
    def initialize():
        # ディレクトリ作成
        for path in [os.path.dirname(ConfigManager.CONFIG_PATH),
                    os.path.join(ConfigManager.BASE_DIR, "SHINOBI", "assets", "faces"),
                    os.path.join(ConfigManager.BASE_DIR, "SHINOBI", "logs", "audit")]:
            if not os.path.exists(path):
                os.makedirs(path)

        # 設定ファイルの初期化または修復
        if not os.path.exists(ConfigManager.CONFIG_PATH):
            if os.path.exists(ConfigManager.BACKUP_PATH):
                import shutil
                shutil.copy2(ConfigManager.BACKUP_PATH, ConfigManager.CONFIG_PATH)
                logger.info("Config restored from backup.")
            else:
                default_config = {
                    "pin_hash": hashlib.sha256("0000".encode()).hexdigest(),
                    "rssi_threshold": -70,
                    "face_threshold": 0.5,
                    "target_mac": "00:00:00:00:00:00",
                    "smart_mitigation_hours": 1,
                    "heartbeat_interval_mins": 10,
                    "system_version": "3.0.0"
                }
                ConfigManager._write_config(default_config)
                logger.info("Default config created.")

    @staticmethod
    def get(key):
        if not os.path.exists(ConfigManager.CONFIG_PATH):
            ConfigManager.initialize()
        try:
            with open(ConfigManager.CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f).get(key)
        except Exception as e:
            logger.error(f"Read config error: {e}")
            return None

    @staticmethod
    def set(key, value):
        try:
            if not os.path.exists(ConfigManager.CONFIG_PATH):
                ConfigManager.initialize()
            with open(ConfigManager.CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
            config[key] = value
            ConfigManager._write_config(config)
            import shutil
            shutil.copy2(ConfigManager.CONFIG_PATH, ConfigManager.BACKUP_PATH)
        except Exception as e:
            logger.error(f"Write config error: {e}")

    @staticmethod
    def _write_config(config):
        with open(ConfigManager.CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

    @staticmethod
    def verify_pin(pin):
        stored_hash = ConfigManager.get("pin_hash")
        return hashlib.sha256(pin.encode()).hexdigest() == stored_hash
