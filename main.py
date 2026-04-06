import os
import sys

# プロジェクトルートとSHINOBI/srcをパスに追加
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "SHINOBI", "src")

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# 相対インポートを避け、SHINOBI.src.main を直接インポート
try:
    import main as shinobi_core
    # 循環インポートや名前衝突を避けるための属性チェック
    if not hasattr(shinobi_core, 'ShinobiApp'):
        # すでに root の main が読み込まれている場合、src/main を再ロード
        import importlib
        import sys
        if 'main' in sys.modules:
            del sys.modules['main']
        import main as shinobi_core
except Exception:
    from SHINOBI.src.main import ShinobiApp as ShinobiAppClass
    class Dummy: pass
    shinobi_core = Dummy()
    shinobi_core.ShinobiApp = ShinobiAppClass

if __name__ == "__main__":
    app = shinobi_core.ShinobiApp()
    app.run()
