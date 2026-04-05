import os
import sys
import subprocess
import shutil

def build_shinobi():
    """
    SHINOBI 究極版 統合ビルド・自動化スクリプト。
    """
    print("--- SHINOBI ULTIMATE v3.5 BUILDER ---")

    # 1. クリーンアップ
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            print(f"[+] Cleaning {folder}...")
            shutil.rmtree(folder)

    # 2. 依存関係
    print("[+] Checking dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    except Exception as e:
        print(f"[!] Pip install failed: {e}")
        return

    # 3. PyInstaller 実行
    print("[+] Compiling binary with PyInstaller...")
    # ソースと資産を同梱
    # --collect-all は face_recognition / dlib の重いデータを確実に含めるため
    cmd = [
        "pyinstaller",
        "--noconsole",
        "--onefile",
        "--clean",
        "--add-data", "SHINOBI/src;SHINOBI/src",
        "--add-data", "SHINOBI/assets/mobile_key;SHINOBI/assets/mobile_key",
        "--collect-all", "face_recognition",
        "--collect-all", "face_recognition_models",
        "--name", "SHINOBI_ULTIMATE_PRO",
        os.path.join("SHINOBI", "src", "main.py")
    ]

    try:
        subprocess.check_call(cmd)
        print("\n--- BUILD SUCCESSFUL ---")
        print(f"Location: {os.path.abspath('dist/SHINOBI_ULTIMATE_PRO.exe')}")
    except Exception as e:
        print(f"\n[!] Build FAILED: {e}")

if __name__ == "__main__":
    build_shinobi()
