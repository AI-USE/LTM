@echo off
setlocal
echo.
echo  ##########################################################
echo  #                                                        #
echo  #      SHINOBI ULTIMATE - HACKER EDITION BUILDER         #
echo  #                                                        #
echo  ##########################################################
echo.

:: 依存関係のチェックとインストール
echo [1/4] Installing dependencies...
pip install -r requirements.txt

:: ビルドコマンドの実行
echo [2/4] Compiling SHINOBI to Binary...
:: --onefile: 1つの実行ファイルにまとめる
:: --noconsole: 起動時にコマンドプロンプトを出さない
:: --add-data: 資産ファイルを含める (Windowsはセミコロン区切り)
:: --clean: 一時ファイルを削除

pyinstaller --noconsole --onefile --clean ^
    --add-data "SHINOBI/src;SHINOBI/src" ^
    --add-data "SHINOBI/assets;SHINOBI/assets" ^
    --name "SHINOBI_HACKER_EDITION" ^
    SHINOBI/src/main.py

echo.
echo [3/4] Build process finished.
echo Output: dist/SHINOBI_HACKER_EDITION.exe

echo.
echo [4/4] Post-build instructions:
echo  - Run as Administrator for full Registry/Shell features.
echo  - Recovery keys should be kept separately.
echo.
pause
endlocal
