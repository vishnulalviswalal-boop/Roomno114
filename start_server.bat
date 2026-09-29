@echo off
title Room 114 Kirana Server & Live Tunnel
cd /d "%~dp0"

echo ========================================================
echo   Room No 114 Kirana Store - Live Multi-Partner Server
echo ========================================================
echo.

:: Check if server is already running on port 8080
netstat -ano | findstr :8080 >nul
if %errorlevel% equ 0 (
    echo Python server is already running on port 8080.
) else (
    echo Starting Python Server on port 8080...
    start "Room 114 Kirana Server" /min python server.py
    timeout /t 2 /nobreak >nul
)

:: Check if cloudflared is running
tasklist /fi "imagename eq cloudflared.exe" | findstr /i "cloudflared.exe" >nul
if %errorlevel% equ 0 (
    echo Cloudflare tunnel is already running.
) else (
    echo Starting Cloudflare Live Tunnel...
    start "Room 114 Cloud Tunnel" .\cloudflared.exe tunnel --url http://localhost:8080
)

echo.
echo Local Counter PC: http://localhost:8080
echo Shop Wi-Fi:      http://10.187.3.226:8080/index.html
echo.
echo Live Tunnel window is open in background.
pause
