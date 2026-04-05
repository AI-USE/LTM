import os
import sys
import subprocess
import shutil

def run_build():
    """
    SHINOBI v4.0 統合ビルド・パッケージングスクリプト。
    """
    print("==============================================")
    print("   SHINOBI v4.0 ULTIMATE - BUILD SYSTEM")
    print("==============================================")

    # 1. 環境クリーンアップ
    for d in ['build', 'dist']:
        if os.path.exists(d):
            print(f"[+] Removing old {d} directory...")
            shutil.rmtree(d)

    # 2. 依存関係の確実なインストール
    print("[+] Resolving dependencies from requirements.txt...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    except Exception as e:
        print(f"[!] Dependency resolution FAILED: {e}")
        return

    # 3. メインバイナリのビルド
    print("[+] Compiling SHINOBI_ULTIMATE_CORE...")
    cmd_core = [
        "pyinstaller",
        "--noconsole",
        "--onefile",
        "--clean",
        "--add-data", "SHINOBI/src;SHINOBI/src",
        "--add-data", "SHINOBI/assets/mobile_key;SHINOBI/assets/mobile_key",
        "--collect-all", "face_recognition",
        "--collect-all", "face_recognition_models",
        "--collect-all", "customtkinter",
        "--name", "SHINOBI_CORE_v4",
        os.path.join("SHINOBI", "src", "main.py")
    ]

    # 4. ウォッチドッグバイナリのビルド
    print("[+] Compiling SHINOBI_WATCHDOG_GUARD...")
    cmd_guard = [
        "pyinstaller",
        "--noconsole",
        "--onefile",
        "--clean",
        "--name", "SHINOBI_GUARD_v4",
        os.path.join("SHINOBI", "src", "watchdog_runner.py")
    ]

    try:
        subprocess.check_call(cmd_core)
        subprocess.check_call(cmd_guard)
        print("\n==============================================")
        print("   BUILD COMPLETED SUCCESSFULLY")
        print(f"   Core: dist/SHINOBI_CORE_v4.exe")
        print(f"   Guard: dist/SHINOBI_GUARD_v4.exe")
        print("==============================================")
    except Exception as e:
        print(f"\n[!] Compilation FAILED: {e}")

if __name__ == "__main__":
    run_build()
