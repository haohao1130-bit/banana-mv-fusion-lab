# 🍌 BANANAMV FUSION LAB

**Classic × VNext 融合實驗室（Public / Experimental）**

> ⚠️ 這是獨立實驗倉庫，**不是**正式 Classic，也不是 VNext 主線。
> 第一階段先從已恢復的 Classic MAIN 建立可執行基底，再逐項引入並驗證 VNext 的有效能力；**目前尚未聲稱完成融合**。

## 官方入口

- **Fusion Lab Colab**：[BANANAMV_FUSION_LAB.ipynb](https://colab.research.google.com/github/haohao1130-bit/banana-mv-fusion-lab/blob/main/BANANAMV_FUSION_LAB.ipynb)
- **Classic 正式公開版**：[banana-mv-public](https://github.com/haohao1130-bit/banana-mv-public)
- **Classic 私人版**：[banana-mv-colab](https://github.com/haohao1130-bit/banana-mv-colab)
- **VNext 研究版**：[banana-mv-vnext](https://github.com/haohao1130-bit/banana-mv-vnext)
- **27B 模型比較試煉場**：[banana-grandmaster-27b](https://github.com/haohao1130-bit/banana-grandmaster-27b)

## 開發原則

1. 保留 Classic 的原生 H3 9B 導演自由度、低延遲、素材、原曲與合成路徑。
2. 只吸收 VNext 已被證實有用的分段事件／狀態交接；不整包導入多輪審稿架構。
3. 首要驗收：不能預演未來事件、不能無故重演過去事件、服裝及道具變化按分段時間嚴格延續。
4. 以實際 9B 時間、JSON 成功率、事件連續性、拍攝稿多樣性、H3 影片結果比較，不把 mock 測試等同 GPU 實測。
5. **Classic／VNext／27B 的 GitHub 倉庫與各自資料完全不修改。**

詳細範圍、版本來源與逐步驗收請見 [docs/FUSION_PLAN.md](docs/FUSION_PLAN.md)。

## 執行與資料隔離

- Colab 筆記本：`BANANAMV_FUSION_LAB.ipynb`
- Colab checkout：`/content/banana-mv-fusion-lab`
- Colab 專案資料：`MyDrive/BananaMVFusionLab`
- Windows checkout：`%USERPROFILE%\banana-mv-fusion-lab`
- Windows 專案資料：`%LOCALAPPDATA%\BananaMVFusionLab`
- Windows Web：`http://127.0.0.1:8192`
- 共用現有 ComfyUI：`http://127.0.0.1:8000`，不再建立另一套模型下載環境。

第一次請只用短歌曲、480P、「先搓丹方」檢查，不要直接投入長影片 GPU 額度。新 GitHub 倉庫的離線 CI 驗證並非 Colab GPU 驗證。

## 構建與離線測試

```bash
python -m pip install Pillow numpy ipywidgets
python tools/build_notebook.py
python -m unittest discover -s tests
node tests/check_ui.cjs
```

建置後可用 `git diff --exit-code BANANAMV_FUSION_LAB.ipynb` 驗證筆記本與產生器同步。

## 來源與授權

本實驗倉庫的初始程式基底取自 `haohao1130-bit/banana-mv-public` 的 main；與 VNext 保持獨立。專案整合程式依 [LICENSE](LICENSE)；第三方模型、外掛、文件依 [THIRD_PARTY.md](THIRD_PARTY.md) 各自授權。
