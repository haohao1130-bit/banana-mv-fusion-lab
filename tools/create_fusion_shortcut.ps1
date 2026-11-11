$ErrorActionPreference = 'Stop'
$shell = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$shortcut = $shell.CreateShortcut((Join-Path $desktop 'BANANAMV Fusion Lab CU130.lnk'))
$shortcut.TargetPath = Join-Path $PSScriptRoot 'start_fusion_local.cmd'
$shortcut.WorkingDirectory = Split-Path -Parent $PSScriptRoot
$shortcut.Description = 'Fusion Lab Banana MV, current branch auto-update, existing CU130 ComfyUI'
$shortcut.Save()
Write-Host 'Created BANANAMV Fusion Lab CU130 desktop shortcut. The launcher reuses or starts CU130 ComfyUI.'
