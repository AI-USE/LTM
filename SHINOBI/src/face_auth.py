import cv2
import face_recognition
import numpy as np
import os
import pickle
import time
import logging

logger = logging.getLogger("SHINOBI.FaceAuth")

class FaceAuth:
    """
    顔認証システム（マルチサンプル対応）
    """
    def __init__(self, data_path=None, threshold=0.5):
        if data_path is None:
            # SHINOBI/assets/faces
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(base_dir, "assets", "faces")

        self.data_path = data_path
        self.threshold = threshold
        self.known_face_encodings = []
        self.known_face_names = []
        self.load_known_faces()

    def load_known_faces(self):
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
            return

        self.known_face_encodings = []
        self.known_face_names = []
        for filename in os.listdir(self.data_path):
            if filename.endswith(".pkl"):
                try:
                    with open(os.path.join(self.data_path, filename), 'rb') as f:
                        encoding = pickle.load(f)
                        self.known_face_encodings.append(encoding)
                        self.known_face_names.append(filename)
                except Exception as e:
                    logger.error(f"Error loading face profile {filename}: {e}")

        logger.info(f"Loaded {len(self.known_face_encodings)} face samples.")

    def capture_frame(self):
        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            logger.error("Camera not available.")
            return None

        ret, frame = video_capture.read()
        video_capture.release()
        return frame if ret else None

    def register_face(self, name_prefix="user"):
        frame = self.capture_frame()
        if frame is None: return False

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if len(encodings) > 0:
            encoding = encodings[0]
            filepath = os.path.join(self.data_path, f"{name_prefix}_{int(time.time())}.pkl")
            with open(filepath, 'wb') as f:
                pickle.dump(encoding, f)
            self.load_known_faces()
            logger.info(f"New face registered: {filepath}")
            return True
        return False

    def authenticate(self, frame=None):
        """
        実戦的な顔認証照合ロジック。
        """
        if frame is None:
            frame = self.capture_frame()
        if frame is None:
            logger.warning("Auth skipped: No camera frame.")
            return False, 1.0

        if not self.known_face_encodings:
            logger.warning("Auth skipped: No known faces.")
            return False, 1.0

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        unknown_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if not unknown_encodings:
            logger.info("No face detected in auth frame.")
            return False, 1.0

        unknown_encoding = unknown_encodings[0]
        # 登録済みエンコーディングとの距離を計算
        face_distances = face_recognition.face_distance(self.known_face_encodings, unknown_encoding)

        if len(face_distances) == 0:
            return False, 1.0

        min_distance = min(face_distances)
        is_match = min_distance < self.threshold
        logger.info(f"Face Auth - Distance: {min_distance:.4f}, Threshold: {self.threshold}, Match: {is_match}")

        return is_match, min_distance

    def set_threshold(self, value):
        self.threshold = value

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fa = FaceAuth()
    # fa.register_face()
