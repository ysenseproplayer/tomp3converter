# YouTube MP3 Downloader - Web Server
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ffmpegBin = Join-Path $projectRoot "ffmpeg-master-latest-win64-gpl\bin"
$pythonPath = Join-Path $projectRoot "python-3.12\python.exe"
$appPath = Join-Path $projectRoot "app.py"

# Add FFmpeg to PATH
$env:PATH = "$ffmpegBin;$env:PATH"

Write-Host "Starting YouTube MP3 Downloader web server..." -ForegroundColor Green
Write-Host "Open your browser and go to: http://localhost:5000" -ForegroundColor Cyan
Write-Host ""

& $pythonPath $appPath
