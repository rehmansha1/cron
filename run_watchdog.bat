@echo off
title Career Watchdog - 1-Hour Telegram Job Monitor
cd /d "%~dp0"
python main.py watch --interval 1h -q
pause
