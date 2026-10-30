# PowerShell script to launch all three services in separate background jobs or windows
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Starting Unified Business Assistant (Role A + B + C)..." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$baseDir = $PSScriptRoot
$pythonExe = Join-Path $baseDir "venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$env:PREFER_MOCK = "false" 

# Start Role A
Start-Process -FilePath $pythonExe -ArgumentList "-m uvicorn app:app --host 127.0.0.1 --port 8000" -WorkingDirectory $baseDir -WindowStyle Minimized
Write-Host "[+] Role A (Knowledge Service) starting on http://127.0.0.1:8000" -ForegroundColor Green

# Start Role B
Start-Process -FilePath $pythonExe -ArgumentList "-m uvicorn app_role_b:app --host 127.0.0.1 --port 8001" -WorkingDirectory $baseDir -WindowStyle Minimized
Write-Host "[+] Role B (Data Service) starting on http://127.0.0.1:8001" -ForegroundColor Green

# Start Role C
Start-Process -FilePath $pythonExe -ArgumentList "-m uvicorn app_role_c:app --host 127.0.0.1 --port 8002" -WorkingDirectory $baseDir -WindowStyle Normal
Write-Host "[+] Role C (Orchestrator & UI) starting on http://127.0.0.1:8002" -ForegroundColor Green

Write-Host "`nAll services launched! Access Role C Dashboard at: http://127.0.0.1:8002" -ForegroundColor Yellow
