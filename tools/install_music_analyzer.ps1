param(
    [string]$PythonPath = '',
    [string]$DataRoot = (Join-Path $env:LOCALAPPDATA 'BananaMVFusionLab'),
    [switch]$Force
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $PythonPath) {
    $preferred = Join-Path $env:USERPROFILE 'Documents\ComfyUI\.venv\Scripts\python.exe'
    $fallback = Join-Path $env:LOCALAPPDATA 'Banana9B-cu130\Scripts\python.exe'
    if (Test-Path -LiteralPath $preferred) { $PythonPath = $preferred }
    else { $PythonPath = $fallback }
}
if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    throw "Python was not found: $PythonPath. Provide -PythonPath with your working CU130 Python."
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'Git for Windows is required to install the pinned music analyzer dependencies.'
}
$venvDir = Join-Path $DataRoot 'music-venv'
$installer = Join-Path $projectRoot 'tools\install_music_structure.py'
New-Item -ItemType Directory -Force -Path $DataRoot | Out-Null
Write-Host 'BANANA MV - installing isolated CPU music analyzer'
Write-Host "Music analyzer directory: $venvDir"
$args = @('-u', $installer, '--host-python', $PythonPath, '--venv-dir', $venvDir)
if ($Force) { $args += '--force' }
& $PythonPath @args
if ($LASTEXITCODE -ne 0) {
    throw "Music analyzer installation failed. Check $DataRoot\music_structure_install.log; music analysis is not silently disabled."
}
Write-Host 'Music analyzer is ready. Fusion Lab will use it after restart.'
