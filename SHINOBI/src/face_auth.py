import os
import time
import logging

logger = logging.getLogger("SHINOBI.FaceAuth")

class FaceAuth:
    """
    顔認証システム（マルチサンプル対応）
    """
    def __init__(self, data_path=None, threshold=0.5):
        if data_path is None:
            base_dir = os.getcwd()
            data_path = os.path.join(base_dir, "SHINOBI", "assets", "faces")

        self.data_path = data_path
        self.threshold = threshold
        self.known_face_encodings = []
        self.load_known_faces()

    def load_known_faces(self):
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
            return
        logger.info(f"Face profiles directory: {self.data_path}")

    def capture_frame(self):
        return None

    def register_face(self, name_prefix="user"):
        return False

    def authenticate(self, frame=None, mock_result=False):
        """
        認証の試行。
        """
        # テスト用
        logger.info("Face authenticating...")
        return mock_result, 0.4 if mock_result else 0.8

    def set_threshold(self, value):
        self.threshold = value

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fa = FaceAuth()
