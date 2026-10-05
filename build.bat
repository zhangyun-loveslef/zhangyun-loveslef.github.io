@echo off
rem 一键构建：从 essays/*.md 与 site-config.json 重新生成 index.html
cd /d "%~dp0"
python build.py
pause
