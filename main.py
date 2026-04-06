import os
import sys

# プロジェクトルートとSHINOBI/srcをパスに追加
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

SRC_DIR = os.path.join(ROOT_DIR, "SHINOBI", "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

try:
    from SHINOBI.src.main import ShinobiApp
except ImportError:
    from main import ShinobiApp # パス設定後

if __name__ == "__main__":
    ShinobiApp().run()
