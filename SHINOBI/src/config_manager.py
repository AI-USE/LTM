import os
import json
import hashlib
import sys
import shutil
import logging
from Crypto.Cipher import AES
from Crypto.Util import Counter

logger = logging.getLogger("SHINOBI.SecureConfig")

class ConfigManager:
    """
    SHINOBI v4.0 セキュア構成管理。
    AES-256 暗号化による資産保護、自己修復、EXE対応。
    """
    if getattr(sys, 'frozen', False):
        BASE_DIR = os.path.dirname(sys.executable)
    else:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    ASSETS_DIR = os.path.join(BASE_DIR, "assets")
    FACES_DIR = os.path.join(ASSETS_DIR, "faces")
    LOGS_DIR = os.path.join(BASE_DIR, "logs")
    CONFIG_PATH = os.path.join(ASSETS_DIR, "secure_config.bin") # 暗号化バイナリ
    BACKUP_PATH = os.path.join(ASSETS_DIR, "secure_config_backup.bin")

    # 内部マスターキー（実運用ではマシン固有ID等から生成を推奨）
    _MASTER_KEY = hashlib.sha256(b"SHINOBI_ULTIMATE_v4_AES_KEY").digest()

    @staticmethod
    def initialize():
        os.makedirs(ConfigManager.ASSETS_DIR, exist_ok=True)
        os.makedirs(ConfigManager.FACES_DIR, exist_ok=True)
        os.makedirs(ConfigManager.LOGS_DIR, exist_ok=True)

        if not os.path.exists(ConfigManager.CONFIG_PATH):
            if os.path.exists(ConfigManager.BACKUP_PATH):
                shutil.copy2(ConfigManager.BACKUP_PATH, ConfigManager.CONFIG_PATH)
            else:
                # 初期デフォルト
                default = {
                    "pin_hash": hashlib.sha256("0000".encode()).hexdigest(),
                    "rssi_threshold": -70,
                    "face_threshold": 0.5,
                    "setup_complete": False,
                    "target_mac": "",
                    "browser_token": "INIT",
                    "smart_mitigation_hours": 1,
                    "heartbeat_interval_mins": 10,
                    "reset_request_time": 0, # リセット申請時刻
                    "theme": "Dark"
                }
                ConfigManager.save_all(default)

    @staticmethod
    def _get_cipher():
        return AES.new(ConfigManager._MASTER_KEY, AES.MODE_CTR, counter=Counter.new(128))

    @staticmethod
    def load_all():
        if not os.path.exists(ConfigManager.CONFIG_PATH):
            ConfigManager.initialize()
        try:
            with open(ConfigManager.CONFIG_PATH, "rb") as f:
                encrypted_data = f.read()
            decrypted_data = ConfigManager._get_cipher().decrypt(encrypted_data)
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception as e:
            logger.error(f"Config Load Error (Corrupted?): {e}")
            return {}

    @staticmethod
    def save_all(config_dict):
        try:
            data_str = json.dumps(config_dict, ensure_ascii=False).encode('utf-8')
            encrypted_data = ConfigManager._get_cipher().encrypt(data_str)
            with open(ConfigManager.CONFIG_PATH, "wb") as f:
                f.write(encrypted_data)
            shutil.copy2(ConfigManager.CONFIG_PATH, ConfigManager.BACKUP_PATH)
        except Exception as e:
            logger.error(f"Config Save Error: {e}")

    @staticmethod
    def get(key):
        return ConfigManager.load_all().get(key)

    @staticmethod
    def set(key, value):
        cfg = ConfigManager.load_all()
        cfg[key] = value
        ConfigManager.save_all(cfg)

    @staticmethod
    def verify_pin(pin):
        stored = ConfigManager.get("pin_hash")
        return hashlib.sha256(pin.encode()).hexdigest() == stored
