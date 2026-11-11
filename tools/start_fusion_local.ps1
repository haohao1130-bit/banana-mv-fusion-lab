param(
    [string]$ComfyUrl = 'http://127.0.0.1:8000',
    [int]$Port = 8192,
    [string]$DataRoot = (Join-Path $env:LOCALAPPDATA 'BananaMVFusionLab'),
    [string]$PythonPath = ''
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$comfyRoot = Join-Path $env:USERPROFILE 'Documents\ComfyUI'
$vnextPython = Join-Path $comfyRoot '.venv\Scripts\python.exe'
$cu130Python = Join-Path $env:LOCALAPPDATA 'Banana9B-cu130\Scripts\python.exe'
if (-not $PythonPath) {
    if (Test-Path -LiteralPath $vnextPython) { $PythonPath = $vnextPython }
    else { $PythonPath = $cu130Python }
}
$python = $PythonPath
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Python not found: $python. Use -PythonPath with the interpreter from your working VNext launch."
}
& $python -c 'import PIL, numpy'
if ($LASTEXITCODE -ne 0) { throw "Python lacks Pillow or numpy: $python. Select the same working Python as VNext." }
foreach ($binary in @('ffmpeg','ffprobe')) {
    if (-not (Get-Command $binary -ErrorAction SilentlyContinue)) { throw "$binary is missing from PATH." }
}
# Music structure is enabled by default: install its independent CPU-only
# Python environment before accepting jobs. Skip completed pinned installs.
& "$PSScriptRoot\install_music_analyzer.ps1" -PythonPath $python -DataRoot $DataRoot
if ($LASTEXITCODE -ne 0) { throw 'Music structure analyzer installation failed.' }
$env:BANANA_MUSIC_PYTHON = Join-Path $DataRoot 'music-venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $env:BANANA_MUSIC_PYTHON -PathType Leaf)) {
    throw 'Missing music analyzer Python; Fusion launch aborted.'
}
# Reuse the verified external ComfyUI; NEVER launch a separate ComfyUI here.
# The successfully working VNext/Classic configurations are authoritative
# for service URL and INPUT directory, not merely an assumed port 8000.
$explicitComfyUrl = $PSBoundParameters.ContainsKey('ComfyUrl')
$candidates = @()
if (-not $explicitComfyUrl) {
    foreach ($entry in @(
        @{ Label = 'VNext'; File = (Join-Path $env:LOCALAPPDATA 'BananaMVVNext\config.json') },
        @{ Label = 'Classic'; File = (Join-Path $env:LOCALAPPDATA 'BananaMVClassic\config.json') }
    )) {
        if (-not (Test-Path -LiteralPath $entry.File -PathType Leaf)) { continue }
        try {
            $prior = Get-Content -LiteralPath $entry.File -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($prior.comfy_url -and $prior.comfy_input_dir) {
                $candidates += [pscustomobject]@{
                    Label = $entry.Label
                    Url = [string]$prior.comfy_url
                    InputDir = [string]$prior.comfy_input_dir
                }
            }
        } catch {
            Write-Host "Skipping unreadable $($entry.Label) ComfyUI config: $($_.Exception.Message)"
        }
    }
}
$candidates += [pscustomobject]@{
    Label = $(if ($explicitComfyUrl) { 'Explicit -ComfyUrl' } else { 'Fusion default' })
    Url = $ComfyUrl
    InputDir = (Join-Path $comfyRoot 'input')
}
$working = $null
$checked = @()
foreach ($candidate in $candidates) {
    $url = ([string]$candidate.Url).TrimEnd('/')
    if (-not $url) { continue }
    try {
        $nodes = Invoke-RestMethod -Uri "$url/object_info" -TimeoutSec 5
        $nodeNames = @($nodes.PSObject.Properties.Name)
        $required = @('TextGenerate', 'MiniMaxH3AudioConditioningT8')
        $missing = @($required | Where-Object { $nodeNames -notcontains $_ })
        if ($missing.Count -gt 0) {
            $checked += "$($candidate.Label) $url : missing $($missing -join ', ')"
            continue
        }
        if (-not (Test-Path -LiteralPath $candidate.InputDir -PathType Container)) {
            $checked += "$($candidate.Label) $url : input directory does not exist ($($candidate.InputDir))"
            continue
        }
        $working = $candidate
        $ComfyUrl = $url
        break
    } catch {
        $checked += "$($candidate.Label) $url : not responding"
    }
}
if ($null -eq $working) {
    $details = $checked -join [Environment]::NewLine
    throw ("No verified working H3/T8 ComfyUI was found. Fusion did not start a replacement service." +
           [Environment]::NewLine + $details + [Environment]::NewLine +
           "Start the same CU130 ComfyUI instance used by the working Classic/VNext setup, " +
           "then rerun Fusion. To point to a specific one, use -ComfyUrl.")
}
$comfyInputDir = [string]$working.InputDir
Write-Host "Verified ComfyUI source: $($working.Label)"
Write-Host "Verified T8 node: MiniMaxH3AudioConditioningT8"
Write-Host "ComfyUI URL: $ComfyUrl"
Write-Host "ComfyUI input: $comfyInputDir"
$guideDir = Join-Path $projectRoot 'guides'
$guide = Join-Path $guideDir 'VIDEO_PROMPT_WRITING_GUIDE_ref_en.md'
New-Item -ItemType Directory -Force -Path $guideDir | Out-Null
if (-not (Test-Path -LiteralPath $guide)) {
    $savedGuide = Join-Path $env:LOCALAPPDATA 'BananaMVVNext\guides\VIDEO_PROMPT_WRITING_GUIDE_ref_en.md'
    if (Test-Path -LiteralPath $savedGuide) { Copy-Item -LiteralPath $savedGuide -Destination $guide }
    else { Invoke-WebRequest -UseBasicParsing -Uri 'https://huggingface.co/MiniMaxAI/MiniMax-H3/resolve/main/docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md' -OutFile $guide }
}
New-Item -ItemType Directory -Force -Path $DataRoot | Out-Null
$configPath = Join-Path $DataRoot 'config.json'
$config = [pscustomobject]@{}
if (Test-Path -LiteralPath $configPath) { $config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json }
elseif (Test-Path -LiteralPath (Join-Path $env:LOCALAPPDATA 'BananaMVVNext\config.json')) {
    $previous = Get-Content -LiteralPath (Join-Path $env:LOCALAPPDATA 'BananaMVVNext\config.json') -Raw | ConvertFrom-Json
    if ($null -ne $previous.rewriter) { $config | Add-Member -NotePropertyName 'rewriter' -NotePropertyValue $previous.rewriter }
}
$config | Add-Member -NotePropertyName 'comfy_url' -NotePropertyValue $ComfyUrl -Force
$config | Add-Member -NotePropertyName 'comfy_input_dir' -NotePropertyValue $comfyInputDir -Force
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($configPath, ($config | ConvertTo-Json -Depth 20), $utf8)
$env:BANANA_DATA = $DataRoot
$env:BANANA_PORT = [string]$Port
Write-Host 'BANANA MV FUSION LAB - CU130 - KEEP OPEN'
Write-Host "Repository: $projectRoot"
& git -C $projectRoot branch --show-current
& git -C $projectRoot log -1 --oneline
Write-Host "Data: $DataRoot"
Write-Host "Python: $python"
Write-Host "ffprobe: $((Get-Command ffprobe).Source)"
Write-Host "ComfyUI: $ComfyUrl"
Write-Host "Fusion MV: http://127.0.0.1:$Port"
Write-Host 'Prepare recipe first. Video rendering needs the matching H3 models and Banana audio node.'
Push-Location $projectRoot
try { & $python -u -m banana_mv.server }
finally { Pop-Location }
