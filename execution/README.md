# Execution 目錄

這個目錄包含所有確定性 Python 執行腳本。

## 🎯 設計原則

### 1. 確定性
- 相同輸入應產生相同輸出
- 避免隨機性（除非必要且有種子控制）
- 可預測的錯誤處理

### 2. 可測試性
- 每個函數都應該可以獨立測試
- 使用清晰的輸入/輸出接口
- 包含錯誤處理和驗證

### 3. 可維護性
- 清晰的註解和文檔字符串
- 模組化設計
- 遵循 PEP 8 編碼規範

## 📝 腳本模板

```python
#!/usr/bin/env python3
"""
Script Name: example_script.py
Purpose: [簡短描述腳本功能]
Author: Agent System
Created: [日期]
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """
    Main execution function
    """
    try:
        # Your code here
        print("執行成功")
        return 0
    except Exception as e:
        print(f"錯誤：{str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

## 🔧 通用工具

建議創建以下通用工具腳本：

- `utils/logger.py` - 統一的日誌記錄
- `utils/file_handler.py` - 檔案操作工具
- `utils/api_client.py` - API 調用封裝
- `utils/validator.py` - 輸入驗證工具

## ⚡ 執行方式

```bash
# 直接執行
python execution/script_name.py

# 帶參數執行
python execution/script_name.py --input path/to/input --output path/to/output

# 使用環境變數
python execution/script_name.py
```

## 📊 錯誤處理

所有腳本應該：
1. 返回適當的退出代碼（0=成功，1=錯誤）
2. 將錯誤訊息輸出到 stderr
3. 記錄詳細錯誤信息到日誌文件
4. 提供有用的錯誤提示給用戶
