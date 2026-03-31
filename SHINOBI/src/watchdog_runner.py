import os
import time
import subprocess
import sys
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("SHINOBI.Watchdog")

class ShinobiWatchdog:
    """
    SHINOBI メインプロセスの死活監視。
    """
    def __init__(self, main_process_path):
        self.main_process_path = main_process_path
        self.process = None

    def start_main(self):
        """
        メインプロセスを起動。
        """
        logger.info(f"Starting SHINOBI main process: {self.main_process_path}")
        self.process = subprocess.Popen([sys.executable, self.main_process_path])

    def monitor(self):
        """
        無限ループでプロセスを監視。死んだら即座に再起動。
        """
        self.start_main()
        while True:
            # プロセスが終了したかチェック
            if self.process.poll() is not None:
                logger.warning("SHINOBI main process TERMINATED. RESTARTING IN 0.5s...")
                time.sleep(0.5)
                self.start_main()
            time.sleep(1)

if __name__ == "__main__":
    # このスクリプトは、単体で「監視役」として動作させる。
    # 実機では EXE 化された監視プログラムとして実行することを想定。
    base_dir = os.path.dirname(os.path.abspath(__file__))
    main_path = os.path.join(base_dir, "main.py")

    watchdog = ShinobiWatchdog(main_path)
    try:
        watchdog.monitor()
    except KeyboardInterrupt:
        logger.info("Watchdog shutting down.")
        if watchdog.process:
            watchdog.process.terminate()
