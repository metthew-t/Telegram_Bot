param(
    [switch]$Install = $false
)

# Navigate to project root
$ProjectRoot = $PSScriptRoot

if ($Install) {
    Write-Host "Setting up Python Virtual Environment..." -ForegroundColor Green
    py -m venv venv_local
    
    Write-Host "Installing dependencies..." -ForegroundColor Green
    .\venv_local\Scripts\python.exe -m pip install -r requirements.txt
    
    Write-Host "Running Database Migrations..." -ForegroundColor Green
    cd backend
    ..\venv_local\Scripts\python.exe manage.py migrate
    cd ..
}

Write-Host "Starting Django Backend on port 8000..." -ForegroundColor Yellow
Start-Process -NoNewWindow -FilePath ".\venv_local\Scripts\python.exe" -ArgumentList "backend\manage.py", "runserver", "8000"

Write-Host "Starting Telegram Bot..." -ForegroundColor Yellow
Start-Process -NoNewWindow -FilePath ".\venv_local\Scripts\python.exe" -ArgumentList "bot\telegram_bot.py"

Write-Host "Starting Frontend Server on port 3000..." -ForegroundColor Yellow
Start-Process -NoNewWindow -FilePath ".\venv_local\Scripts\python.exe" -ArgumentList "server.py"

Write-Host "All services started!" -ForegroundColor Green
Write-Host "Frontend is running at http://localhost:3000"
Write-Host "Backend API is running at http://localhost:8000"
Write-Host "To stop services, you can close the terminal or use Task Manager."
