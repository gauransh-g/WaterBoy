@echo off
title WaterBoy Launcher
echo ========================================================
echo   Starting WaterBoy Groundwater Intelligence Platform
echo ========================================================

echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000...
start "WaterBoy Backend (FastAPI)" cmd /k "python backend\run_server.py"

echo [2/2] Starting React + Vite Frontend on http://127.0.0.1:5173...
start "WaterBoy Frontend (Vite)" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================================
echo   WaterBoy servers are launching!
echo   - Frontend UI:  http://127.0.0.1:5173
echo   - Backend API: http://127.0.0.1:8000
echo   - API Docs:    http://127.0.0.1:8000/docs
echo ========================================================
echo Opening browser in 3 seconds...
ping 127.0.0.1 -n 4 >nul
start http://127.0.0.1:5173
