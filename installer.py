import os
import sys
import subprocess
import shutil

def run_ultimate_build():
    """
    SHINOBI v4.2 究極版 統合ビルドシステム。
    CORE と GUARD の両バイナリを一発で生成。
    """
    print("==============================================")
    print("   SHINOBI v4.2 ULTIMATE - BUILD COMMAND")
    print("==============================================")

    # クリーンアップ
    for d in ['build', 'dist']:
        if os.path.exists(d): shutil.rmtree(d)

    # 依存関係
    print("[+] 依存関係を解決中...")
    try:
        # Windows 固有のライブラリや暗号化ライブラリを確実に導入
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pycryptodome", "bleak", "customtkinter", "opencv-python", "face-recognition", "qrcode[pil]"])
        if os.name == 'nt':
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32"])
    except Exception as e:
        print(f"[!] 依存関係のインストールに失敗しました: {e}")

    # メインバイナリ (CORE)
    print("[+] SHINOBI_CORE をビルド中 (数分かかります)...")
    cmd_core = [
        "pyinstaller", "--noconsole", "--onefile", "--clean",
        "--add-data", "SHINOBI;SHINOBI",
        "--add-data", "SHINOBI/assets/mobile_key;SHINOBI/assets/mobile_key",
        "--collect-all", "face_recognition",
        "--collect-all", "face_recognition_models",
        "--collect-all", "customtkinter",
        "--name", "SHINOBI_CORE_v4.2",
        "main.py"
    ]

    # 監視バイナリ (GUARD)
    print("[+] SHINOBI_GUARD をビルド中...")
    cmd_guard = [
        "pyinstaller", "--noconsole", "--onefile", "--clean",
        "--name", "SHINOBI_GUARD_v4.2",
        os.path.join("SHINOBI", "src", "watchdog_runner.py")
    ]

    try:
        subprocess.check_call(cmd_core)
        subprocess.check_call(cmd_guard)
        print("\n==============================================")
        print("   究極版ビルド完了")
        print(f"   コア: dist/SHINOBI_CORE_v4.2.exe")
        print(f"   監視: dist/SHINOBI_GUARD_v4.2.exe")
        print("==============================================")
    except Exception as e:
        print(f"\n[!] ビルド失敗: {e}")

if __name__ == "__main__":
    run_ultimate_build()
