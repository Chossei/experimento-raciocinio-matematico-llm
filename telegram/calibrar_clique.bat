@echo off
title Calibrar Posicao do Chat - Antigravity IDE
chcp 65001 >nul

cd /d "%~dp0\.."

"C:\Users\choss\AppData\Local\Programs\Python\Python312\python.exe" "telegram\calibrar_posicao.py"

pause
