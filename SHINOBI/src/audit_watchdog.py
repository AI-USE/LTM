import os
import sqlite3
import time
import datetime
import cv2
import logging

logger = logging.getLogger("SHINOBI.Audit")

class AuditLog:
    """
    7日間のローテーション監査ログ（実画像 + DB）。
    """
    def __init__(self, db_path=None, img_dir=None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = db_path or os.path.join(base_dir, "logs", "audit.db")
        self.img_dir = img_dir or os.path.join(base_dir, "logs", "audit")

        self._init_db()
        self.cleanup_old_logs()

    def _init_db(self):
        if not os.path.exists(os.path.dirname(self.db_path)):
            os.makedirs(os.path.dirname(self.db_path))
        if not os.path.exists(self.img_dir):
            os.makedirs(self.img_dir)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                route TEXT,
                face_img_path TEXT,
                status TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def log_entry(self, route, face_img_frame=None, status="SUCCESS"):
        """
        ログを記録。顔写真がある場合は保存。
        """
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        img_filename = f"{timestamp_str}.jpg"
        img_path = os.path.join(self.img_dir, img_filename)

        # 実際にOpenCVでフレームを保存（引数がない場合はカメラから取得を試みる）
        if face_img_frame is not None:
            cv2.imwrite(img_path, face_img_frame)
        else:
            video_capture = cv2.VideoCapture(0)
            if video_capture.isOpened():
                ret, frame = video_capture.read()
                if ret:
                    cv2.imwrite(img_path, frame)
                video_capture.release()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO audit_logs (route, face_img_path, status)
            VALUES (?, ?, ?)
        ''', (route, img_path, status))
        conn.commit()
        conn.close()

        logger.info(f"Audit log added: {route} - {status}")

    def cleanup_old_logs(self, days=7):
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT face_img_path FROM audit_logs WHERE timestamp < ?", (cutoff_str,))
        old_files = cursor.fetchall()

        for (f_path,) in old_files:
            if os.path.exists(f_path):
                os.remove(f_path)

        cursor.execute("DELETE FROM audit_logs WHERE timestamp < ?", (cutoff_str,))
        conn.commit()
        conn.close()

class Watchdog:
    """
    プロセスの死活監視。
    """
    def __init__(self, main_process_name="SHINOBI_HACKER_EDITION.exe"):
        self.main_process_name = main_process_name

    def monitor(self):
        # 実機では別プロセス（EXE）として動き、psutil等を使用して監視
        logger.info(f"Watchdog initialized: Monitoring {self.main_process_name}...")
        pass
