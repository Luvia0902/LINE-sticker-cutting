# 快速開始指南

## 🎯 目標
這份指南將幫助您在 5 分鐘內開始使用 LINE 貼圖切割 Agent 系統。

## 📦 步驟 1：環境設置

### 1.1 安裝 Python 依賴
```bash
pip install -r requirements.txt
```

### 1.2 配置環境變數（可選）
```bash
copy .env.example .env
# 然後編輯 .env 填入您的 API 金鑰
```

## 🖼️ 步驟 2：準備您的貼圖圖片

將您要切割的大圖放在 `.tmp/input/` 目錄下：
```bash
mkdir .tmp\input
# 將您的圖片複製到 .tmp\input\sticker_sheet.png
```

**圖片要求：**
- 格式：PNG
- 建議尺寸：1850x1280 像素（370×5 x 320×4）
- 包含：20 張貼圖，排列為 4 行 5 列

## ⚙️ 步驟 3：執行切割

```bash
python execution\split_stickers.py --input .tmp\input\sticker_sheet.png --output .tmp\output\stickers
```

**參數說明：**
- `--input` / `-i`: 輸入圖片路徑
- `--output` / `-o`: 輸出目錄（預設：`.tmp/output/stickers`）
- `--rows` / `-r`: 行數（預設：4）
- `--cols` / `-c`: 列數（預設：5）

## ✅ 步驟 4：檢查結果

切割完成後，您會在輸出目錄看到 20 張貼圖：
```
.tmp/output/stickers/
├── sticker_01.png
├── sticker_02.png
├── ...
└── sticker_20.png
```

每張貼圖：
- 尺寸：370x320 像素
- 格式：PNG
- 已優化壓縮

## 🚀 進階使用

### 自訂切割配置
如果您的貼圖排列不是 4x5：

```bash
# 3 行 3 列（9 張貼圖）
python execution\split_stickers.py -i input.png -o output -r 3 -c 3

# 2 行 4 列（8 張貼圖）
python execution\split_stickers.py -i input.png -o output -r 2 -c 4
```

### 批次處理
如果您有多張圖片要處理：

```powershell
# PowerShell
Get-ChildItem .tmp\input\*.png | ForEach-Object {
    $name = $_.BaseName
    python execution\split_stickers.py -i $_.FullName -o ".tmp\output\$name"
}
```

## 📚 下一步

- 閱讀 `agent.md` 了解完整的 Agent 架構
- 查看 `directives/example_directive.md` 了解如何編寫任務指令
- 探索 `execution/` 目錄了解更多可用工具

## ❓ 常見問題

### Q: 圖片檔案太大怎麼辦？
A: 腳本會自動優化壓縮。如果仍超過 1MB，您可能需要：
- 降低原始圖片品質
- 減少透明度複雜度
- 使用更簡單的圖案

### Q: 可以切割其他尺寸的貼圖嗎？
A: 目前腳本使用 LINE 官方規格（370x320）。如需其他尺寸，請修改 `execution/split_stickers.py` 中的 `STICKER_SIZE` 常數。

### Q: 支援其他圖片格式嗎？
A: 目前僅支援 PNG。LINE 貼圖需要透明背景，因此必須使用 PNG 格式。

## 🆘 遇到問題？

1. 檢查錯誤訊息
2. 確認圖片格式和路徑正確
3. 查看日誌檔案：`.tmp/logs/agent.log`
4. 回報問題時請附上完整的錯誤訊息

---

**現在開始使用吧！** 🎉
