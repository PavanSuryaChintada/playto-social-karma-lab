# Setup script - handles paths with spaces (e.g. "git repos")
# Run from project root: .\setup.ps1

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$requirementsPath = Join-Path $projectRoot "backend\requirements.txt"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment..."
    python -m venv (Join-Path $projectRoot ".venv")
}

Write-Host "Installing dependencies..."
& $venvPython -m pip install -r $requirementsPath
Write-Host "Done. Activate with: .\.venv\Scripts\Activate.ps1"
