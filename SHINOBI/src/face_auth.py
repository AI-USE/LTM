import os
import time
import logging

logger = logging.getLogger("SHINOBI.FaceAuth")

class FaceAuth:
    """
    顔認証システム（マルチサンプル対応）
    """
    def __init__(self, data_path=None, threshold=0.5):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = data_path or os.path.join(base_dir, "assets", "faces")
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
        return True

    def authenticate(self, frame=None, mock_result=False):
        """
        認証の試行。
        """
        logger.info("Face authenticating...")
        return mock_result, 0.4 if mock_result else 0.8

    def authenticate_async(self, callback):
        callback(True, 0.4)

    def set_threshold(self, value):
        self.threshold = value

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fa = FaceAuth()
