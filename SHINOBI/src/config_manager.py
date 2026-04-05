import os
import json
import hashlib
import logging
import sys

logger = logging.getLogger("SHINOBI.Config")

class ConfigManager:
    """
    SHINOBI 構成管理モジュール (EXE対応版)。
    """
    # 実行ファイルのディレクトリを取得（EXE化された場合も対応）
    if getattr(sys, 'frozen', False):
        # EXEとして実行されている場合
        BASE_DIR = os.path.dirname(sys.executable)
    else:
        # スクリプトとして実行されている場合
        # SHINOBI/src/config_manager.py なので、2つ上がルート
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 書き込み可能なアセットパスの設定
    ASSETS_DIR = os.path.join(BASE_DIR, "assets")
    FACES_DIR = os.path.join(ASSETS_DIR, "faces")
    LOGS_DIR = os.path.join(BASE_DIR, "logs")

    CONFIG_PATH = os.path.join(ASSETS_DIR, "config.json")
    BACKUP_PATH = os.path.join(ASSETS_DIR, "config_backup.json")
    AUDIT_DB_PATH = os.path.join(LOGS_DIR, "audit.db")

    @staticmethod
    def initialize():
        # 必要なディレクトリを全て作成
        for path in [ConfigManager.ASSETS_DIR, ConfigManager.FACES_DIR, ConfigManager.LOGS_DIR]:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)

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
                    "setup_complete": False,
                    "browser_token": "DEFAULT",
                    "system_version": "3.4.0"
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
