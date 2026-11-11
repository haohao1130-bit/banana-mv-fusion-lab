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
    throw "找不到 Python：$PythonPath。請指定 -PythonPath 為可用的 CU130 Python。"
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw '音樂結構分析器需要 Git 下載固定版本依賴，請先安裝 Git for Windows。'
}
$venvDir = Join-Path $DataRoot 'music-venv'
$installer = Join-Path $projectRoot 'tools\install_music_structure.py'
New-Item -ItemType Directory -Force -Path $DataRoot | Out-Null
Write-Host '🍌 安裝 Python 音樂結構耳朵（All-In-One CPU 隔離環境）'
Write-Host "分析器位置：$venvDir"
$args = @('-u', $installer, '--host-python', $PythonPath, '--venv-dir', $venvDir)
if ($Force) { $args += '--force' }
& $PythonPath @args
if ($LASTEXITCODE -ne 0) {
    throw '音樂結構分析器安裝失敗，請查看 DataRoot\music_structure_install.log；不會關閉分析功能假裝成功。'
}
Write-Host '✅ 音樂結構分析器安裝完成。重新啟動 Fusion Lab 後自動使用。'
