import os
import json
import hashlib
import sys
import shutil
import logging
import platform
import subprocess
from Crypto.Cipher import AES
from Crypto.Util import Counter

logger = logging.getLogger("SHINOBI.Config")

class ConfigManager:
    """
    SHINOBI v4.2 構成管理。
    パス解決の完全自動化と AES 暗号化。
    """
    # 実行ファイルまたはスクリプトのディレクトリを正確に取得
    if getattr(sys, 'frozen', False):
        BASE_DIR = os.path.dirname(sys.executable)
        SRC_DIR = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    else:
        # SHINOBI/src に配置されていることを想定
        SRC_DIR = os.path.dirname(os.path.abspath(__file__))
        BASE_DIR = os.path.dirname(SRC_DIR)

    ASSETS_DIR = os.path.join(BASE_DIR, "assets")
    FACES_DIR = os.path.join(ASSETS_DIR, "faces")
    LOGS_DIR = os.path.join(BASE_DIR, "logs")
    CONFIG_PATH = os.path.join(ASSETS_DIR, "secure_config.bin")
    BACKUP_PATH = os.path.join(ASSETS_DIR, "secure_config_backup.bin")
    AUDIT_DB_PATH = os.path.join(LOGS_DIR, "audit.db")

    @staticmethod
    def _get_hardware_id():
        """デバイス固有のIDを取得し、暗号化キーの生成に使用する。"""
        try:
            if platform.system() == "Windows":
                cmd = 'reg query "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography" /v MachineGuid'
                output = subprocess.check_output(cmd, shell=True).decode()
                return output.split()[-1]
            else:
                import uuid
                return str(uuid.getnode())
        except Exception:
            return "SHINOBI_FALLBACK_ID_777"

    _MASTER_KEY = hashlib.sha256(
        (b"SHINOBI_V4.2_SALT_" + _get_hardware_id.__func__().encode())
    ).digest()

    @staticmethod
    def initialize():
        # インポートパスの調整
        if ConfigManager.SRC_DIR not in sys.path:
            sys.path.insert(0, ConfigManager.SRC_DIR)

        os.makedirs(ConfigManager.ASSETS_DIR, exist_ok=True)
        os.makedirs(ConfigManager.FACES_DIR, exist_ok=True)
        os.makedirs(ConfigManager.LOGS_DIR, exist_ok=True)

        if not os.path.exists(ConfigManager.CONFIG_PATH):
            if os.path.exists(ConfigManager.BACKUP_PATH):
                shutil.copy2(ConfigManager.BACKUP_PATH, ConfigManager.CONFIG_PATH)
            else:
                default = {
                    "pin_hash": hashlib.sha256("0000".encode()).hexdigest(),
                    "rssi_threshold": -70,
                    "face_threshold": 0.5,
                    "setup_complete": False,
                    "target_mac": "",
                    "browser_token": "INIT",
                    "smart_mitigation_hours": 1,
                    "heartbeat_interval_mins": 10,
                    "reset_request_time": 0,
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
            logger.error(f"構成ロードエラー: {e}")
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
            logger.error(f"構成保存エラー: {e}")

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
