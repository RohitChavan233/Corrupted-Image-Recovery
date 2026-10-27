@echo off
title Photorecover - Image Viewer & Recovery Suite
echo ========================================================
echo Starting Photorecover (XnView MP Modern Rebuild)
echo ========================================================

echo [1/2] Starting Python Backend API on http://127.0.0.1:8765 ...
start "Photorecover Backend" cmd /k "python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765"

timeout /t 2 /nobreak >nul

echo [2/2] Starting React + Vite Frontend on http://localhost:5173 ...
cd frontend
start "Photorecover Frontend" cmd /k "npm run dev"

echo ========================================================
echo App running! Opening browser at http://localhost:5173 ...
echo ========================================================
start http://localhost:5173
pause
