# Fusion V1 — Classic + VNext 最小融合（2026-11-11）

## 狀態

- 基底是 Classic schema-5 的原生 H3 寫咒：保留目前自由運鏡、單一全曲規劃、逐段原生六區塊攝影稿、T8 原曲、補拍與續跑。
- `banana_mv/creative_contract.py` 完整移植自 VNext：只在一次全曲分配讀取 RELATION/DUTY 與禁止分屏的政策。沒有額外 9B 模型呼叫。
- `banana_mv/fusion_state.py` 以 Python 計算連續快照，引用舊 `scene_state.GARMENT_EDGES` 與 `STATUSES`。**不進入舊版 `ensure_scene_state` / `update_scene_memory` 重型模型路徑**。
- Fusion V1 新任務寫入 `scene_state_version=3`、`persistent_scene_state=True`；舊任務使用保存的版本欄位，不被升級。
- CI 靜態與 mock GPU 驗收通過不等於 5070、Colab G4 或 H3 成片已實測。

## 單次 9B 全曲分配：狀態標記

原始分段大綱仍是 `=== SETUP ===`、`=== STORY OUTCOME ===`、
`=== CLIP N mode ===`、`=== END ===`。

如果本段確實有衣物狀態變化，就在本段的普通事件敘述**之後**放一個簡短標記：

```text
=== CLIP 0 performance ===
S1 goes on stage and takes off her jacket.
[[STATE S1.jacket:worn>removed]]
=== CLIP 1 performance ===
S1 removes her top as the background changes.
[[STATE S1.top:worn>removed]]
=== CLIP 2 performance ===
S1 continues in the current outfit; no new garment transition.
=== END ===
```

Python 將標記從攝影委託中移除，驗證 `from → to` 是合法邊，計算每段 `in`／`changes`／`out`，並將進入狀態與**本段唯一授權變化**傳給現有逐段攝影寫手。其餘未指定的狀態不推測；角色穿著由狀態而不是原圖初始衣著決定。

`director_plan.json` 保存每段的 `fusion_state`。因此中斷續跑會沿用已分配的確定性狀態，不會重新向 9B 問「上一段發生什麼」。這些是**計畫狀態，不是 H3 生成結果的視覺辨識**。

同時，靜態使用者契約僅流到**全曲分配**階段；`STORY OUTCOME` 不直接流給中段攝影寫手。

## 結局鎖

- 按 `mv_scope.clip_ending()` 既有來源歌曲契約判斷；`phase=continuing` 才禁止不屬於該段的全劇勝負。
- `phase=resolving` 才能執行**此段已分配**的決勝事件；不是要求每段各 KO 一次。
- 當原曲尾段 ≤ 3 秒時，按舊規定由**倒數第二段**完成關鍵事件，尾段只有後果／延續畫面；不可生硬規定唯有最後一段才能分勝負。
- `project_scope=excerpt` 仍可出現局部事件結果，不會強迫完整作品結局。

## 模型呼叫與性能

Fusion V1 新任務將 `rewrite_retries` 設為 0，核心寫稿嚴格最多 1 次全曲規劃＋每段 1 次攝影。失敗清楚報錯，不做暗中多輪重試；**若使用者另外要求繁中丹方翻譯，翻譯本身是額外的選填 9B 作業，不計入核心寫稿預算**。續跑的顯式重試／更換專案和 GPU 渲染是另一個工作週期。

狀態轉移計算本身無額外模型呼叫，但不是實際 0 秒的測量值。**RTX 5070 在 45 秒內完成 4 段 9B 寫稿**需本機實測，不由 CI 保證。

## 限制與下一輪可改進

1. Python 僅驗證**已標注**的狀態轉移；若 9B 忘記輸出標記，不能憑空推斷所有服裝、道具和傷勢。這輪先追蹤**衣物類**，其他實體的通用狀態方案屬下一步。
2. No split-screen、禁止提前 KO 和「不要重演」是**寫稿輸入規則**，不是成片視覺分析或語意全知的硬保證。
3. 標記不是複雜 JSON，但仍依賴全曲分配者正確指出發生在哪一段；Python 只確定性計算轉移，無法取代事件語意判斷。
4. STATE 前綴盡量短，但狀態過多時不任意截斷關鍵事實來硬達字數上限。
5. A/B 比較應固定音源、Seed、角色素材、模型權重與分段設定，統計 JSON 成功率、9B 實測延遲、劇情重演、外觀時間軸與最終 H3 影片，而非只檢查是否有禁止字句。

## 回滾

以 PR 單獨合併。若 Fusion 新任務品質退化，可在 Fusion 倉庫 revert 該 PR；
Classic／VNext 源碼與 Drive 資料未改。
