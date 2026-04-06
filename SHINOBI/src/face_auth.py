import os
import time
import logging
import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("SHINOBI.FaceAuth")

# 遅延ロード: face_recognition は重いため、使用時にのみインポートを試みる
# (本番環境では bundled 版に含まれる)
face_recognition = None
try:
    import face_recognition as fr
    # 一部の環境で import 自体は成功しても内部エラーが出るのを防ぐ
    if hasattr(fr, 'face_encodings'):
        face_recognition = fr
except Exception:
    face_recognition = None

class FaceAuth:
    """顔認証システム v4.2 (実機動作対応版)"""
    def __init__(self, threshold=None):
        from config_manager import ConfigManager
        self.data_path = ConfigManager.FACES_DIR
        self.threshold = threshold or ConfigManager.get("face_threshold") or 0.5
        self.known_encodings = []
        self._executor = ThreadPoolExecutor(max_workers=1)
        self.load_known_faces()

    def load_known_faces(self):
        """保存されている顔データからエンコーディングをロード。"""
        if not face_recognition: return
        self.known_encodings = []
        try:
            for file in os.listdir(self.data_path):
                if file.endswith(".npy"):
                    enc = np.load(os.path.join(self.data_path, file))
                    self.known_encodings.append(enc)
            logger.info(f"Loaded {len(self.known_encodings)} face templates.")
        except Exception as e:
            logger.error(f"Failed to load faces: {e}")

    def register_face(self, frame):
        """現在のフレームから顔を登録（学習）。"""
        if not face_recognition or frame is None: return False
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(rgb_frame)
            if encodings:
                timestamp = int(time.time())
                save_path = os.path.join(self.data_path, f"face_{timestamp}.npy")
                np.save(save_path, encodings[0])
                self.known_encodings.append(encodings[0])
                logger.info(f"New face registered: {save_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False

    def authenticate(self, frame):
        """
        同期認証。
        戻り値: (bool 成功か, float 最小距離)
        """
        if not face_recognition or frame is None or not self.known_encodings:
            return False, 1.0

        try:
            # 処理高速化のためリサイズ
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            min_dist = 1.0
            found = False

            for face_encoding in face_encodings:
                # 既知の顔データ全てと比較
                distances = face_recognition.face_distance(self.known_encodings, face_encoding)
                if len(distances) > 0:
                    current_min = min(distances)
                    min_dist = min(min_dist, current_min)
                    if current_min < self.threshold:
                        found = True
                        break

            return found, float(min_dist)
        except Exception as e:
            logger.error(f"Auth error: {e}")
            return False, 1.0

    def authenticate_async(self, frame, callback):
        """非同期で認証を行い、結果をコールバック。"""
        def task():
            success, dist = self.authenticate(frame)
            callback(success, dist)
        self._executor.submit(task)

    def set_threshold(self, value):
        self.threshold = float(value)

if __name__ == "__main__":
    fa = FaceAuth()
