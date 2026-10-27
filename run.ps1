# PowerShell Launcher for Photorecover
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Starting Photorecover (XnView MP Modern Rebuild)" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

Write-Host "[1/2] Starting Python Backend API on http://127.0.0.1:8765..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765"

Start-Sleep -Seconds 2

Write-Host "[2/2] Starting React + Vite Frontend on http://localhost:5173..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'r:\GitHub EXp\Photorecover\frontend'; npm run dev"

Start-Sleep -Seconds 2
Start-Process "http://localhost:5173"
Write-Host "Photorecover launched successfully!" -ForegroundColor Green
