@echo off
setlocal
echo.
echo  ##########################################################
echo  #                                                        #
echo  #      SHINOBI ULTIMATE v3.0 - PROFESSIONAL BUILDER      #
echo  #                                                        #
echo  ##########################################################
echo.

:: 依存関係のチェック
echo [1/4] Installing necessary dependencies...
pip install -r requirements.txt
pip install customtkinter darkdetect

:: ビルドコマンド
echo [2/4] Compiling SHINOBI professional binary...
:: --onefile: 単一実行ファイル
:: --noconsole: コンソール非表示 (UIアプリ)
:: --clean: 一時ファイル削除
:: --add-data: 資産フォルダの同梱

pyinstaller --noconsole --onefile --clean ^
    --add-data "SHINOBI/src;SHINOBI/src" ^
    --add-data "SHINOBI/assets;SHINOBI/assets" ^
    --name "SHINOBI_ULTIMATE_v3" ^
    SHINOBI/src/main.py

echo.
echo [3/4] Build process completed successfully.
echo Output: dist/SHINOBI_ULTIMATE_v3.exe

echo.
echo [4/4] Setup instructions:
echo  - Execute as Administrator to enable Registry/Shell protections.
echo  - Review README.md for initial setup and recovery steps.
echo.
pause
endlocal
