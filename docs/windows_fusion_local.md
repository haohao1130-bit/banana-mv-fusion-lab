# Windows｜Fusion Lab 本機啟動

1. `git clone --branch main https://github.com/haohao1130-bit/banana-mv-fusion-lab.git "$env:USERPROFILE\\banana-mv-fusion-lab"`
2. 已有 VNext 或 Classic 的 ComfyUI（預設 `http://127.0.0.1:8000`）先啟動。
3. 進入 `$env:USERPROFILE\\banana-mv-fusion-lab`，執行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\\tools\\create_fusion_shortcut.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\\tools\\start_fusion_local.ps1"
```

預設：`http://127.0.0.1:8192`；資料：`%LOCALAPPDATA%\\BananaMVFusionLab`；重用你原本的 VNext Python 或 CU130 Python。不覆寫 Classic `8191`、VNext `8190`、既有設定或模型。

Fusion 短時可與舊前端並存，但不要讓多個服務同時對一個 ComfyUI GPU 送影片工作。若有不同的 Python 路徑，傳給 `start_fusion_local.ps1 -PythonPath "C:\\path\\to\\python.exe"`。

手機遠端如使用 Tailscale Serve，請另選新 HTTPS 埠（例如 `8444`），不要覆寫 VNext `443` 或 Classic `8443`；只在確認該埠空閒後設定。
