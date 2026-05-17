# build.ps1 — Windows build script
# Run: .\build.ps1

Write-Host "=== Building assistant for Windows ===" -ForegroundColor Cyan

# Clean previous build
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

# Run PyInstaller
pyinstaller assistant.spec --noconfirm

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=== Build successful! ===" -ForegroundColor Green
    Write-Host "Binary: dist\assistant\assistant.exe" -ForegroundColor Green
    Write-Host ""
    Write-Host "NOTE: Copy your .env file next to assistant.exe before running." -ForegroundColor Yellow
    Write-Host "NOTE: Whisper/Silero models will download on first run (~500MB)." -ForegroundColor Yellow
} else {
    Write-Host "=== Build FAILED ===" -ForegroundColor Red
    exit 1
}
