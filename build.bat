@echo off
setlocal enabledelayedexpansion

echo  ----------------------------------------------------------
echo    SHINOBI ULTIMATE v3.4 - ONE-CLICK EXE BUILDER
echo  ----------------------------------------------------------
echo.

:: [1] 古いビルド資産のクリーンアップ
echo [+] Cleaning old build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

:: [2] 依存関係のチェックとインストール
echo [+] Checking dependencies...
pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo [!] Failed to install requirements.
    pause
    exit /b !errorlevel!
)

:: [3] ビルド実行
echo [+] Compiling SHINOBI to Binary (This may take several minutes)...
:: --onefile: 実行ファイルを1つに集約
:: --noconsole: 起動時にコンソールを表示しない
:: --collect-all: face_recognition や dlib のモデルを自動収集
:: --add-data: ソースコード以外の資産を同梱 (フォルダ構造を維持)

pyinstaller --noconsole --onefile --clean ^
    --add-data "SHINOBI/src;SHINOBI/src" ^
    --add-data "SHINOBI/assets/mobile_key;SHINOBI/assets/mobile_key" ^
    --collect-all face_recognition ^
    --collect-all face_recognition_models ^
    --name "SHINOBI_ULTIMATE_v3.4" ^
    SHINOBI/src/main.py

if !errorlevel! neq 0 (
    echo.
    echo [!] Build FAILED. Check the error messages above.
    pause
    exit /b !errorlevel!
)

echo.
echo  ----------------------------------------------------------
echo    BUILD SUCCESSFUL!
echo    Location: dist/SHINOBI_ULTIMATE_v3.4.exe
echo  ----------------------------------------------------------
echo.
echo  NOTE:
echo  - Run as Administrator to enable full Windows OS protection.
echo  - Ensure webcam and Bluetooth are functional on your system.
echo.
pause
endlocal
