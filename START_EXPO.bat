@echo off
title UrbanEye Expo Master Launcher
echo ==============================================
echo    URBANEYE EXPO STARTUP - READY TO WOW!
echo ==============================================
echo.

:: 1. Start Backend
echo [1/4] Launching BACKEND ENGINE...
start "UrbanEye-Backend" cmd /k "cd /d %~dp0backend && python app.py"
timeout /t 5

:: 2. Start Tunnel (Self-Healing Mode)
echo [2/4] Launching PUBLIC TUNNEL (Bridge to Mobile)...
start "UrbanEye-Tunnel" cmd /k "cd /d %~dp0 && LAUNCH_TUNNEL.bat"
timeout /t 5

:: 3. Start AI Agent
echo [3/4] Launching AUTONOMOUS AI AGENT...
start "UrbanEye-AI-Agent" cmd /k "cd /d %~dp0backend && python ai/autonomous_agent.py"
timeout /t 2

:: 4. Start Admin Dashboard
echo [4/4] Launching ADMIN DASHBOARD (Map View)...
start "UrbanEye-Admin" cmd /k "cd /d %~dp0admin-dashboard && npm.cmd start"

echo.
echo ==============================================
echo    ALL SYSTEMS LIVE! 🛡️🚀
echo    Keep these windows open during the Expo.
echo ==============================================
pause
