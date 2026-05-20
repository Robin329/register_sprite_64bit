@echo off
REM 双击或命令行运行均可；所有打包逻辑在 build.py 中。
REM 可传参数，例如：build_for_win.bat --console --onedir
cd /d %~dp0
python build.py %*
pause
