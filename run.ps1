# YouTube MP3 Downloader - Run Script
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ffmpegBin = Join-Path $projectRoot "ffmpeg-master-latest-win64-gpl\bin"
$pythonPath = Join-Path $projectRoot "python-3.12\python.exe"
$mainPath = Join-Path $projectRoot "main.py"

# Add FFmpeg to PATH
$env:PATH = "$ffmpegBin;$env:PATH"

# Check if URL is provided as argument
if ($args.Count -gt 0) {
    & $pythonPath $mainPath $args[0]
} else {
    & $pythonPath $mainPath
}
