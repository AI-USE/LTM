import os
import sqlite3
import time
import datetime
import cv2
import logging
from config_manager import ConfigManager

logger = logging.getLogger("SHINOBI.Audit")

class AuditLog:
    """
    監査ログ (堅牢版)。
    """
    def __init__(self):
        self.db_path = ConfigManager.AUDIT_DB_PATH
        self.img_dir = os.path.join(ConfigManager.LOGS_DIR, "audit_imgs")
        self._init_db()

    def _init_db(self):
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            os.makedirs(self.img_dir, exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, route TEXT, face_img_path TEXT, status TEXT)''')
        except Exception as e:
            logger.error(f"DB初期化エラー: {e}")

    def log_entry(self, route, face_img_frame=None, status="SUCCESS"):
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        img_path = os.path.join(self.img_dir, f"{timestamp_str}.jpg")

        try:
            if face_img_frame is not None:
                cv2.imwrite(img_path, face_img_frame)
            else:
                # 監査用の写真撮影
                cap = cv2.VideoCapture(0, cv2.CAP_DSHOW if os.name == 'nt' else 0)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret: cv2.imwrite(img_path, frame)
                    cap.release()

            with sqlite3.connect(self.db_path) as conn:
                conn.execute('INSERT INTO audit_logs (route, face_img_path, status) VALUES (?, ?, ?)', (route, img_path, status))
            logger.info(f"監査ログを記録しました: {route}")
        except Exception as e:
            logger.error(f"ログ記録エラー: {e}")

    def cleanup_old_logs(self, days=7):
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT face_img_path FROM audit_logs WHERE timestamp < ?", (cutoff,))
                for (f_path,) in cursor.fetchall():
                    if os.path.exists(f_path): os.remove(f_path)
                cursor.execute("DELETE FROM audit_logs WHERE timestamp < ?", (cutoff,))
        except Exception as e:
            logger.error(f"ログクリーンアップエラー: {e}")
