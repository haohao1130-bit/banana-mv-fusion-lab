# 🍌 Fusion Lab｜實驗總表

## 基底與隔離（2026-11-11）

- 完整起點：`haohao1130-bit/banana-mv-public` main，版本 `083d87e74f5321479bd8998783e563a08c9c4f58`（Classic 的正式恢復線）。
- 參照研究：`haohao1130-bit/banana-mv-vnext` main，版本 `0684b2d23b13325f12520c77e0858b2070793cab`。
- 本倉不追蹤原本遠端 git 分支，也不修改原本四個倉庫。
- **階段 0 為 Classic 完整複製與環境隔離，尚未植入 VNext 功能。** 不可把它稱為已融合成品。
- Colab 程式 checkout 與 Drive 保存分離；本機獨立 Git／專案資料／Web 埠，ComfyUI 與已下載的權重可共用（勿同時提交 GPU 工作）。
- 原有 `PUBLIC_MANIFEST.json` 是舊倉快照，不能挪用來證明 Fusion 檔案雜湊，因此不搬入。

## 先驗收的五組題

1. **事件不能偷跑**：例如拳擊勝負已指定於 70–80 秒，不可在 0–10 秒判勝。上游可看完整故事，下游只拿當段事件。
2. **狀態不能倒退**：角色上一段摘下的衣物／丟下的道具，下一段從現況開始；沒有明確取回事件不得復原。
3. **狀態不能超前**：下一段預定變化不得提前發生；拆段後為每段傳入 `appearance_in`、`allowed_changes`、`appearance_out`。
4. **跨段鏡頭可連續又不重演**：事件因果與機位/動能交接，而非重複前段高潮，允許不同場景切換。
5. **原曲時長權威**：完整結局依音訊時間；僅 ≤3 秒的最後短尾視為餘韻，完成的事件須在前一段成立。

## 技術路線

**Phase 0 — Classic Clone**（本次初始化）：完整 Classic 後端、前端、測試、H3/T8、9B 本地改寫和 Colab 開爐流程。更換 Repo、Colab 筆記本名稱、Drive 資料根和 Windows 啟動埠，保持導演語義不變。

**Phase 1 — 輕量事件帳本**：擷取 VNext 的 `Opening state / New progression / Outgoing state` 當段交接理念，以全曲一次規劃產生順序化事件；下游只拿當段允許的事件，不加一輪 9B 語意審核。

**Phase 2 — 狀態時間軸**：物件/衣物/受傷等持續變化改成薄層資料，使用穩定 ID 和狀態轉移，依演出事件記錄起點與終點。**不是重新啟用 Classic 舊 `scene_state_version=1` 重型流程**。只在故事確實有變化時附上局部狀態。

**Phase 3 — 真正的攝影交接**：從 VNext 引入已被觀察有用的動態接鏡資料；保留 Classic 的自由分鏡（不可固定鏡頭數或模版運鏡）。

**Phase 4 — A/B 報告**：同歌曲、Seed、參考圖和故事分別跑 Classic、Fusion。分別記錄時間、9B 呼叫數、段落完成與漏拍、重複動作、角色與衣物狀態、輸出影片效果。

## 時間軸狀態範例（作為驗收資料，不是自動產生裸體內容的指令）

- S1 初始：`{coat:worn, top:worn, bottom:worn}`
- 片段 1：`allowed=[remove(coat)]` → `{coat:removed, top:worn, bottom:worn}`
- 片段 2：`allowed=[remove(top)]` → `{coat:removed, top:removed, bottom:worn}`
- 片段 3：`allowed=[remove(bottom)]` → `{coat:removed, top:removed, bottom:removed}`
- 片段 4：`allowed=[]` → 狀態維持，沒有新衣物或自動還原。

此處只驗證**寫稿與結構化狀態**，不宣稱 H3 影像已經能完全遵循。

## 不准混淆的實作層次

- 上游一次分配全曲與事件；
- 下游只接收局部拍攝委託與當前狀態；
- H3 最終生成仍有模型不確定性；
- 模擬測試通過 ≠ 實際 Colab GPU 或 RTX 5070 錄製成功；
- 低結構衣物僅用於劇情連續性，不以服裝本身主導運鏡與場景。
