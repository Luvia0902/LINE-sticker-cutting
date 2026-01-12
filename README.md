# LINE 貼圖切割 Agent 系統

這是一個基於三層架構的 Agent 自動化系統，用於處理 LINE 貼圖相關任務。

## 🏗️ 架構概述

### 三層架構
1. **指令層** (`directives/`) - 定義任務的 SOP（標準操作程序）
2. **編排層** - AI Agent 負責智慧路由和決策
3. **執行層** (`execution/`) - 確定性 Python 腳本

## 📁 目錄結構

```
LINE貼圖切割20張/
├── agent.md              # Agent 核心指令文檔
├── directives/           # 任務指令集（SOP）
├── execution/            # Python 執行腳本
├── .tmp/                 # 臨時文件（可重新生成）
├── .env                  # 環境變數（請勿提交）
├── .env.example          # 環境變數模板
└── README.md            # 本文件
```

## 🔍 系統健康檢查

首次安裝後，運行健康檢查確保所有組件正常：

```bash
python check_system.py
```

此腳本會驗證：
- ✓ 所有必要文件和目錄
- ✓ Python 腳本完整性
- ✓ 核心依賴是否安裝

## 🚀 快速開始

### 1. 環境設置

```bash
# 安裝 Python 依賴
pip install -r requirements.txt

# 複製環境變數模板（可選）
copy .env.example .env

# 編輯 .env 填入您的 API 金鑰（可選）
```

### 2. 安裝依賴

```bash
pip install -r requirements.txt
```

### 3. 創建您的第一個指令

在 `directives/` 目錄下創建 Markdown 文件，例如 `directives/split_line_stickers.md`

### 4. 創建對應的執行腳本

在 `execution/` 目錄下創建 Python 腳本，例如 `execution/split_stickers.py`

### 5. 使用 GUI 工具（推薦新手）

我們提供了圖形化介面版本，適合視覺化操作：

```bash
python execution\sticker_splitter_gui.py
```

**GUI 功能**：
- ✅ 點擊式操作，無需命令列
- ✅ 即時預覽圖片和切割網格
- ✅ 精確規格支援（2560×1664，4×5）
- ✅ 進度條和狀態提示

**詳細教學**：[`GUI_QUICKSTART.md`](GUI_QUICKSTART.md)

## 📝 如何使用

1. **定義任務**：在 `directives/` 中創建 SOP 文檔
2. **讓 AI 編排**：AI Agent 讀取指令並決定執行順序
3. **自動執行**：調用 `execution/` 中的 Python 腳本
4. **自我修復**：遇到錯誤時自動修復並更新指令

## 🔧 操作原則

- ✅ **先檢查工具**：使用現有腳本，避免重複造輪子
- ✅ **自我修復**：遇到錯誤時自動修正並更新文檔
- ✅ **持續改進**：將學到的經驗更新到指令中

## 📚 更多信息

詳細的 Agent 操作指令請參閱 `agent.md` 文件。

## ⚠️ 注意事項

- `.tmp/` 目錄中的所有文件都可以刪除並重新生成
- 請勿將 `.env`、`credentials.json`、`token.json` 提交到版本控制
- 最終交付物應儲存在雲端服務（Google Sheets、Slides 等）
