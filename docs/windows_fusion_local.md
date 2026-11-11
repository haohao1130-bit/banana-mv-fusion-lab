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


## 🎧 音樂結構分析器（Python 的耳朵）

Fusion V2 的「音樂結構分析（BPM／拍點／主歌／副歌）」預設開啟，
Windows 啟動器 \`tools/start_fusion_local.ps1\` 現在會先呼叫
\`tools/install_music_analyzer.ps1\`。只有首次缺少依賴或固定版更新時才安裝；
平常啟動只做輕量 import 檢查。

獨立分析環境：

- \`%LOCALAPPDATA%\BananaMVFusionLab\music-venv\Scripts\python.exe\`
- 安裝日誌：\`%LOCALAPPDATA%\BananaMVFusionLab\music_structure_install.log\`
- 環境變數 \`BANANA_MUSIC_PYTHON\` 由 Windows 啟動器自動設定
- 分析器 \`all-in-one-infer\` 固定 Git revision：\`566f96c3f007c783ab5eb6db0123bf3335af8f31\`
- 使用 CPU，不另佔 ComfyUI 的 GPU；不卸載或升級既有 H3／9B 的 CU130 PyTorch
- 首次**分析歌曲**還可能下載 All-In-One 與 Demucs 模型權重；它們不是 H3 的模型

如果之前已在 0/N 段遇到「分析器尚未安裝」，先關掉 Fusion 伺服器，更新主倉：

\`\`\`powershell
git -C "$env:USERPROFILE\banana-mv-fusion-lab" pull --ff-only origin main
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\banana-mv-fusion-lab\tools\install_music_analyzer.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\banana-mv-fusion-lab\tools\start_fusion_local.ps1"
\`\`\`

第一個啟動命令會自動重用已完成的音樂依賴安裝。若失敗，請先查看
\`music_structure_install.log\`，**不會靜默關閉音樂結構分析**。

Colab 不使用 Windows 這份安裝器；Colab 的①安裝格本來就會呼叫
\`install_music_analysis()\`，安裝在專案下的 \`.music-venv/bin/python\`。
已經進入前端才發現沒有安裝時，請重新執行 Colab 的①，再啟動③。
首次 CPU 歌曲分析所需時間另計，不等同 Python 切歌和 SRT 對齊時間。
