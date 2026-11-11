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


## 連接已成功的 Classic／VNext H3 T8 ComfyUI

Fusion \`8192\`、Classic \`8191\`、VNext \`8190\` 是**前端服務埠**；
它們不等於 ComfyUI 的工作流 API 服務埠。

Fusion 啟動器不再自行開啟另一個 ComfyUI。它會按順序檢查：
- \`%LOCALAPPDATA%\BananaMVVNext\config.json\` 的 \`comfy_url\`、\`comfy_input_dir\`
- \`%LOCALAPPDATA%\BananaMVClassic\config.json\` 的相同欄位
- 預設 \`http://127.0.0.1:8000\` 與 \`%USERPROFILE%\Documents\ComfyUI\input\`

只有同時提供 \`TextGenerate\` 和 \`MiniMaxH3AudioConditioningT8\`，
而且指定的本地 \`input\` 目錄存在的實例，才可讓 Fusion 繼續開爐。
選中的 ComfyUI 位址和 input 目錄會顯示在啟動視窗並寫入 Fusion 自己的設定，
不改動原本成功的 Classic／VNext 設定。

遇到「缺少 MiniMaxH3AudioConditioningT8」時，**不應直接重裝模型**；
先檢查目前在提供服務的 ComfyUI：

\`\`\`powershell
$nodes = Invoke-RestMethod 'http://127.0.0.1:8000/object_info'
$nodes.PSObject.Properties.Name -contains 'MiniMaxH3AudioConditioningT8'
$nodes.PSObject.Properties.Name -contains 'TextGenerate'
Get-Content "$env:LOCALAPPDATA\BananaMVVNext\config.json" -Raw
\`\`\`

若第一個結果為 \`False\`，表示**目前該位址提供服務的 ComfyUI 沒有註冊 T8 節點**。
它可能是啟動了不同 ComfyUI，或 T8 外掛載入失敗；
不能單憑這個訊息認定插件沒安裝。先重新啟動你已成功跑過的那套
CU130／T8 ComfyUI，然後再啟動 Fusion；必要時指定：

\`\`\`powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\tools\start_fusion_local.ps1" -ComfyUrl 'http://127.0.0.1:8000' -ComfyRoot "$env:USERPROFILE\Documents\ComfyUI"
\`\`\`

真正的 **本機未提交分支、桌面安裝實例與執行時載入失敗日誌**不會自動同步到 GitHub；
GitHub 同步的程式碼只能用來推斷可能的啟動路徑。若仍找不到節點，需要查看
ComfyUI 啟動視窗中的 custom-node import failure 與實際 \`/object_info\`。
