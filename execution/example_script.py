#!/usr/bin/env python3
"""
Script Name: example_script.py
Purpose: 範例執行腳本 - 展示標準腳本結構
Author: Agent System
Created: 2026-01-11
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def validate_input(input_path):
    """
    驗證輸入檔案
    
    Args:
        input_path: 輸入檔案路徑
        
    Returns:
        bool: 驗證是否通過
    """
    if not Path(input_path).exists():
        print(f"錯誤：輸入檔案不存在：{input_path}", file=sys.stderr)
        return False
    return True

def process_data(input_path, output_path):
    """
    處理數據的主要邏輯
    
    Args:
        input_path: 輸入檔案路徑
        output_path: 輸出檔案路徑
        
    Returns:
        bool: 處理是否成功
    """
    try:
        # 在這裡實現您的處理邏輯
        print(f"正在處理：{input_path}")
        
        # 確保輸出目錄存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        print(f"輸出結果至：{output_path}")
        return True
        
    except Exception as e:
        print(f"處理失敗：{str(e)}", file=sys.stderr)
        return False

def main():
    """
    主執行函數
    """
    parser = argparse.ArgumentParser(description='範例執行腳本')
    parser.add_argument('--input', '-i', required=True, help='輸入檔案路徑')
    parser.add_argument('--output', '-o', required=True, help='輸出檔案路徑')
    parser.add_argument('--verbose', '-v', action='store_true', help='顯示詳細信息')
    
    args = parser.parse_args()
    
    if args.verbose:
        print("詳細模式已啟用")
    
    # 驗證輸入
    if not validate_input(args.input):
        return 1
    
    # 處理數據
    if not process_data(args.input, args.output):
        return 1
    
    print("✓ 執行成功")
    return 0

if __name__ == "__main__":
    sys.exit(main())
