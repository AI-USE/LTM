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
    監査ログ (EXE対応)。
    """
    def __init__(self):
        self.db_path = ConfigManager.AUDIT_DB_PATH
        self.img_dir = os.path.join(ConfigManager.LOGS_DIR, "audit_imgs")
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.img_dir, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute('''CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, route TEXT, face_img_path TEXT, status TEXT)''')
        conn.close()

    def log_entry(self, route, face_img_frame=None, status="SUCCESS"):
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        img_path = os.path.join(self.img_dir, f"{timestamp_str}.jpg")

        if face_img_frame is not None:
            cv2.imwrite(img_path, face_img_frame)
        else:
            video_capture = cv2.VideoCapture(0)
            if video_capture.isOpened():
                ret, frame = video_capture.read()
                if ret: cv2.imwrite(img_path, frame)
                video_capture.release()

        conn = sqlite3.connect(self.db_path)
        conn.execute('INSERT INTO audit_logs (route, face_img_path, status) VALUES (?, ?, ?)', (route, img_path, status))
        conn.commit()
        conn.close()
        logger.info(f"Audit log stored: {route}")

    def cleanup_old_logs(self, days=7):
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT face_img_path FROM audit_logs WHERE timestamp < ?", (cutoff,))
        for (f_path,) in cursor.fetchall():
            if os.path.exists(f_path): os.remove(f_path)
        cursor.execute("DELETE FROM audit_logs WHERE timestamp < ?", (cutoff,))
        conn.commit()
        conn.close()
