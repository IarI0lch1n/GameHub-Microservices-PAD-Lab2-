$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Error "Virtual environment not found: $python"
    exit 1
}


function Start-GameHubService {
    param(
        [string]$Name,
        [string]$Module,
        [int]$Port
    )

    Write-Host "Starting $Name on port $Port" -ForegroundColor Cyan

    $command = "& `"$python`" -m uvicorn ${Module}:app --host 127.0.0.1 --port $Port"

    Start-Process powershell.exe `
        -WorkingDirectory $root `
        -ArgumentList @(
            "-NoExit",
            "-Command",
            $command
        )
}


# Start services that other services depend on.

Start-GameHubService `
    -Name "Catalog Service" `
    -Module "services.catalog_service.app.main" `
    -Port 8003

Start-GameHubService `
    -Name "User Service" `
    -Module "services.user_service.app.main" `
    -Port 8002

Start-GameHubService `
    -Name "Library Service" `
    -Module "services.library_service.app.main" `
    -Port 8005

Start-GameHubService `
    -Name "Notification Service" `
    -Module "services.notification_service.app.main" `
    -Port 8007


# Start publishers and services using Catalog.

Start-GameHubService `
    -Name "Auth Service" `
    -Module "services.auth_service.app.main" `
    -Port 8001

Start-GameHubService `
    -Name "Order Service" `
    -Module "services.order_service.app.main" `
    -Port 8004

Start-GameHubService `
    -Name "Review Service" `
    -Module "services.review_service.app.main" `
    -Port 8006


Write-Host ""
Write-Host "Starting API Gateway..." -ForegroundColor Yellow

Start-Sleep -Seconds 5

Start-GameHubService `
    -Name "API Gateway" `
    -Module "gateway.app.main" `
    -Port 8000


Write-Host ""
Write-Host "GameHub services were launched." -ForegroundColor Green
Write-Host "Gateway: http://127.0.0.1:8000"
Write-Host "Status:  http://127.0.0.1:8000/services/status"