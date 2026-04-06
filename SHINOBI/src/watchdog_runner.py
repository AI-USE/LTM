import os
import time
import subprocess
import sys
import logging
import threading

# ロギング
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] Watchdog: %(message)s')
logger = logging.getLogger("SHINOBI.DoubleGuard")

class DoubleGuard:
    """
    相互監視プロセス (Double-Guard)。
    メインプログラムが落ちた場合、0.5秒以内に再起動する。
    """
    def __init__(self, target_path):
        self.target_path = target_path
        self.process = None

    def launch_target(self):
        logger.info(f"Launching protected target: {self.target_path}")
        # GUIアプリとしてコンソールを表示せずに起動
        if sys.platform == "win32":
            self.process = subprocess.Popen([sys.executable, self.target_path], creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            self.process = subprocess.Popen([sys.executable, self.target_path])

    def monitor_loop(self):
        self.launch_target()
        while True:
            # プロセスの生存確認
            if self.process.poll() is not None:
                logger.error("Protected process TERMINATED unexpectedy!")
                logger.info("Initiating RECOVERY sequence in 0.5s...")
                time.sleep(0.5)
                self.launch_target()
            time.sleep(1) # CPU負荷を抑えるためのインターバル

if __name__ == "__main__":
    # このスクリプトは単独のEXE(shinobi_guard.exe等)としてビルドされる。
    if len(sys.argv) < 2:
        # デフォルトは同階層の main.py (開発時)
        target = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
    else:
        target = sys.argv[1]

    guard = DoubleGuard(target)
    try:
        guard.monitor_loop()
    except KeyboardInterrupt:
        logger.info("Guard shutting down.")
        if guard.process: guard.process.terminate()
