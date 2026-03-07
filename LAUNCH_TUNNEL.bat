@echo off
title UrbanEye Tunnel Monitor
:loop
echo ==============================================
echo [EXPO] Starting Public Tunnel...
echo ==============================================
cd /d d:\UrbanEye\backend
npx localtunnel --port 5000
echo.
echo ⚠️ TUNNEL CRASHED or CLOSED! 
echo Restarting in 5 seconds (Press Ctrl+C to stop)...
timeout /t 5
goto loop
