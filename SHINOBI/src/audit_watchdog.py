import os
import sqlite3
import time
import datetime
import shutil

class AuditLog:
    """
    7日間のローテーション監査ログ（顔写真＋データベース）。
    """
    def __init__(self, db_path="SHINOBI/logs/audit.db", img_dir="SHINOBI/logs/audit"):
        self.db_path = db_path
        self.img_dir = img_dir
        self._init_db()
        self.cleanup_old_logs()

    def _init_db(self):
        if not os.path.exists(os.path.dirname(self.db_path)):
            os.makedirs(os.path.dirname(self.db_path))

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
        img_path = f"{self.img_dir}/{timestamp_str}.jpg"

        # 本来はOpenCV等でフレームを保存
        # cv2.imwrite(img_path, face_img_frame)
        with open(img_path, "w") as f:
            f.write("DUMMY IMAGE DATA")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO audit_logs (route, face_img_path, status)
            VALUES (?, ?, ?)
        ''', (route, img_path, status))
        conn.commit()
        conn.close()

        print(f"Logged: {route} - {status}")

    def cleanup_old_logs(self, days=7):
        """
        8日以上前のデータをDBと物理ファイルの両方から削除。
        """
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 削除対象のファイルパスを取得
        cursor.execute("SELECT face_img_path FROM audit_logs WHERE timestamp < ?", (cutoff_str,))
        old_files = cursor.fetchall()

        for (f_path,) in old_files:
            if os.path.exists(f_path):
                os.remove(f_path)
                print(f"Deleted old evidence: {f_path}")

        # DBレコードを削除
        cursor.execute("DELETE FROM audit_logs WHERE timestamp < ?", (cutoff_str,))
        conn.commit()
        conn.close()

class Watchdog:
    """
    相互監視プロセスの概念。
    実際には別ファイル(EXE)として実行され、互いのPIDが死んだら再起動する。
    """
    def __init__(self, main_process_name="shinobi.exe"):
        self.main_process_name = main_process_name

    def monitor(self):
        print(f"Watchdog: Monitoring {self.main_process_name}...")
        # 実際にはpsutil等でプロセスを監視
        # もしプロセスが落ちていれば 0.5秒以内に再起動

if __name__ == "__main__":
    audit = AuditLog()
    audit.log_entry("Stealth (Face+BT)")
    audit.log_entry("Recovery Route (PIN Only)", status="SUCCESS (RED ALERT)")

    # 擬似的なクリーンアップテスト (手動で古い日付を挿入すれば動作確認可能)
    audit.cleanup_old_logs()
