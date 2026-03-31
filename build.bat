@echo off
echo SHINOBI ビルドスクリプトを実行中...
echo PyInstaller を使用して EXE を作成します。

:: 依存関係のチェック
pip install pyinstaller

:: ビルドコマンド
:: --onefile: 単一の実行ファイルにする
:: --noconsole: 起動時にコンソールを表示しない (UIメイン)
:: --icon: アイコンの指定 (あれば)
:: --add-data: 必要なリソース（config.json, assets等）を含める

pyinstaller --noconsole --onefile ^
    --add-data "SHINOBI/assets;SHINOBI/assets" ^
    --add-data "SHINOBI/src;SHINOBI/src" ^
    --name "SHINOBI_ULTIMATE" ^
    SHINOBI/src/main.py

echo.
echo ビルドが完了しました。
echo dist/SHINOBI_ULTIMATE.exe を管理者権限で実行してください。
pause
