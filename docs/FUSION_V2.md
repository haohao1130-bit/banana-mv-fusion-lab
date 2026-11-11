# 🍌 Fusion V2｜Python Call Sheet × 9B H3 導演

版本：2026-11-11｜測試分支 `feature/fusion-v2-audio-scaffold`

## 核心分工

**Python 是製片主任／場記，9B 是編劇兼 H3 攝影導演。**

- `core.source_audio_duration()` 依已解碼音訊得出真實時長。
- `core.segments()` 以 24 FPS 影格為單位分段，**不由 9B 決定切點**。
- `lyrics_reference.excerpt()` 只映射使用者提供的 SRT 重疊區間，絕不臆造歌詞或口白。
- `audio_analysis.segment_evidence()` 提供相對音量、變化、瞬態候選等客觀線索；可選的 `music_structure` 是預測，並非 Python 從響度推斷的副歌。
- `mv_scope.clip_ending()` 與歌曲來源時間為結局授權權威；≤3 秒短尾只延續已完成結果，指定事件不被機械式「最後一段解鎖」覆蓋。
- **9B 全曲分配仍執行一次**，負責故事、雙線互動與局部事件；V1 `fusion_state.py` 對上游已標記的狀態變化作確定性驗證與傳遞。
- **9B 每段 H3 寫稿一次**，只接收自己的 Call Sheet、官方原生 H3 指南和必要攝影自由度規則；不接收整篇結局。
- 額外翻譯、手動補拍與失敗續跑不屬原始 1＋N 單次規劃測試。

## 新的資料介面

新增 `director_scaffold.build_call_sheet()`，輸出 `FILMING_CALL_SHEET_V2`，同時包含：

| 欄位 | 來源／責任 |
|---|---|
| `frame_window_half_open` | Python 的原始 24 FPS 切片（排除終點） |
| `source_window_s`、`clip_shot_clock_s` | 真正音訊終點和當段可拍秒數（兩者可能差一影格） |
| `user_supplied_srt_clip_local` | Python 擷取的局部 SRT（無字幕不等於靜音） |
| `source_audio` | 量測音訊特徵或明確標成預測的結構 |
| `resolution_gate` | 來源時間契約：ongoing / resolving / terminal_hold / excerpt |
| `physical_state.entry` | V1 Python 狀態機的當段初始事實 |
| `physical_state.authorized_changes_this_clip` | 上游已分配到本段的合法變化 |
| `physical_state.planned_exit` | Python 計算的**計畫**結束狀態，非成片認證 |
| `current_event_only` | 9B 全曲編劇只交付該段事件；不含 STORY OUTCOME |
| `fixed_reference_settings` | 維持人物身份、場景、唱歌職責；無未來劇情 |
| `primary_mode`、`adaptation` | 讓 9B 自由演出，但服從硬限制 |

### 注意：保留 H3 正式輸出契約

**不把官方指南替換成 1KB 攝影字典**。現有專職 Ref2VA 9B 仍須輸出正式六個段落，`detailed_description` 遵守 `[Shot N]`／局部時間碼。不能用只列出鏡頭術語的詞彙表替代這份協議。

V2 將本地每段長管理指令改成精簡的單張 Call Sheet；V1 作為獨立開關的 A/B 基準。

## 版本與比較

創建新 Fusion 任務時：
- `director_scaffold_version=2`（預設）：使用 Python 分段音訊骨架與一張 H3 Call Sheet。
- `director_scaffold_version=0`：保留 Fusion V1 原始段落委託模式，方便實測 A/B。**此為 API 參數，不代表目前前端已提供切換按鈕。**

現有已存專案沿用自身 request 版本，避免開爐、補拍或續跑時偷偷換語義。

`fusion_v2_metrics` 記錄可量測的音訊分析、Scaffold 建構、全曲分配耗時與 `allocation_cached`；每段 `fusion_v2_writer_ms` 記錄寫稿實測耗時。Python 計算不是 0 毫秒，不能由離線 CI 宣稱 RTX 5070 會在 40 秒內完成。

## 驗收

```bash
python -m unittest discover -s tests -v
node tests/check_ui.cjs
python tools/build_notebook.py
git diff --exit-code BANANAMV_FUSION_LAB.ipynb
```

測試包括 58.5 秒/24 FPS、跨段 SRT 長歌詞、62 秒短尾段、預測音樂段落與量測能量區別、狀態不可回滾、純局部 Call Sheet、一次全曲加四段 H3 寫稿、官方指南存在與 V1 相容。

### 真實 RTX 5070 A/B（尚未執行）

同歌曲、角色圖片、模型、seed、CUDA/CU130、重寫參數，以 `director_scaffold_version=0` 對 `2`；記錄來源時長／片段、9B 呼叫數、`fusion_v2_metrics`、每段攝影 prompt、有無重演／偷跑、H3 最終視覺效果與合成音訊精度。不要將純 Python 狀態驗證誤稱為 H3 100% 遵守。
