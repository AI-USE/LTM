import os
import time
import logging

logger = logging.getLogger("SHINOBI.FaceAuth")

class FaceAuth:
    """顔認証システム (テスト用モック)"""
    def __init__(self, threshold=0.5):
        from config_manager import ConfigManager
        self.data_path = ConfigManager.FACES_DIR
        self.threshold = threshold
        self.known_face_encodings = []

    def load_known_faces(self): pass
    def capture_frame(self): return None
    def register_face(self, name_prefix="user"): return True
    def authenticate(self, frame=None, mock_result=False):
        return mock_result, 0.4 if mock_result else 0.8
    def authenticate_async(self, callback):
        callback(True, 0.4)
    def set_threshold(self, value):
        self.threshold = value

if __name__ == "__main__":
    fa = FaceAuth()
