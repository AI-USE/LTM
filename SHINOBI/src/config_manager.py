import os
import json
import hashlib

class ConfigManager:
    """
    設定値とシークレットの管理。
    """
    # 実行ファイルのディレクトリ基準でパスを計算（EXE化対応）
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CONFIG_PATH = os.path.join(BASE_DIR, "assets", "config.json")

    @staticmethod
    def initialize():
        if not os.path.exists(os.path.dirname(ConfigManager.CONFIG_PATH)):
            os.makedirs(os.path.dirname(ConfigManager.CONFIG_PATH))

        if not os.path.exists(ConfigManager.CONFIG_PATH):
            default_config = {
                "pin_hash": hashlib.sha256("0000".encode()).hexdigest(), # デフォルトPIN: 0000
                "browser_token_hash": hashlib.sha256("default_token".encode()).hexdigest(),
                "rssi_threshold": -70,
                "face_threshold": 0.5,
                "target_mac": "00:00:00:00:00:00"
            }
            with open(ConfigManager.CONFIG_PATH, "w") as f:
                json.dump(default_config, f, indent=4)

    @staticmethod
    def get(key):
        if not os.path.exists(ConfigManager.CONFIG_PATH):
            ConfigManager.initialize()
        with open(ConfigManager.CONFIG_PATH, "r") as f:
            return json.load(f).get(key)

    @staticmethod
    def set(key, value):
        with open(ConfigManager.CONFIG_PATH, "r") as f:
            config = json.load(f)
        config[key] = value
        with open(ConfigManager.CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4)

    @staticmethod
    def verify_pin(pin):
        stored_hash = ConfigManager.get("pin_hash")
        return hashlib.sha256(pin.encode()).hexdigest() == stored_hash
