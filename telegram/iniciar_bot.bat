@echo off
title Bot do Telegram - Experimento LLM
chcp 65001 >nul

echo ========================================================
echo   Iniciando Bot de Telemetria do Experimento (Telegram)
echo ========================================================
echo.

cd /d "%~dp0\.."

"C:\Users\choss\AppData\Local\Programs\Python\Python312\python.exe" "telegram\bot_telegram.py"

echo.
echo O bot foi finalizado. Pressione qualquer tecla para sair.
pause >nul
