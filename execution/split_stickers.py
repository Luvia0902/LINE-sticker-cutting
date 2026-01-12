#!/usr/bin/env python3
"""
Script Name: split_stickers.py
Purpose: 將一張大圖切割成多張 LINE 貼圖（20張，4x5 配置）
Author: Agent System
Created: 2026-01-11
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image

# LINE 貼圖官方規格
STICKER_SIZE = (370, 320)  # 寬 x 高
MAX_FILE_SIZE_MB = 1  # 最大檔案大小 1MB

def validate_input_image(image_path):
    """
    驗證輸入圖片
    
    Args:
        image_path: 圖片路徑
        
    Returns:
        tuple: (是否有效, 錯誤訊息)
    """
    if not Path(image_path).exists():
        return False, f"圖片檔案不存在：{image_path}"
    
    try:
        img = Image.open(image_path)
        if img.format != 'PNG':
            return False, f"圖片格式必須是 PNG，目前是：{img.format}"
        return True, None
    except Exception as e:
        return False, f"無法開啟圖片：{str(e)}"

def split_image(input_path, output_dir, rows=4, cols=5):
    """
    切割圖片成多張貼圖
    
    Args:
        input_path: 輸入圖片路徑
        output_dir: 輸出目錄
        rows: 行數
        cols: 列數
        
    Returns:
        int: 成功切割的貼圖數量
    """
    try:
        # 開啟圖片
        img = Image.open(input_path)
        width, height = img.size
        
        # 計算每個貼圖的尺寸
        cell_width = width // cols
        cell_height = height // rows
        
        print(f"原始圖片尺寸：{width} x {height}")
        print(f"每個貼圖尺寸：{cell_width} x {cell_height}")
        print(f"切割配置：{rows} 行 x {cols} 列 = {rows * cols} 張")
        
        # 確保輸出目錄存在
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        count = 0
        # 切割圖片
        for row in range(rows):
            for col in range(cols):
                count += 1
                
                # 計算裁切區域
                left = col * cell_width
                top = row * cell_height
                right = left + cell_width
                bottom = top + cell_height
                
                # 裁切
                sticker = img.crop((left, top, right, bottom))
                
                # 調整為 LINE 貼圖標準尺寸
                sticker_resized = sticker.resize(STICKER_SIZE, Image.Resampling.LANCZOS)
                
                # 儲存
                output_path = Path(output_dir) / f"sticker_{count:02d}.png"
                sticker_resized.save(output_path, 'PNG', optimize=True)
                
                # 檢查檔案大小
                file_size_mb = output_path.stat().st_size / (1024 * 1024)
                if file_size_mb > MAX_FILE_SIZE_MB:
                    print(f"  ⚠ {output_path.name}: {file_size_mb:.2f}MB (超過 {MAX_FILE_SIZE_MB}MB 限制)")
                else:
                    print(f"  ✓ {output_path.name}: {file_size_mb:.2f}MB")
        
        return count
        
    except Exception as e:
        print(f"切割過程發生錯誤：{str(e)}", file=sys.stderr)
        return 0

def main():
    """
    主執行函數
    """
    parser = argparse.ArgumentParser(description='切割圖片為 LINE 貼圖')
    parser.add_argument('--input', '-i', required=True, help='輸入圖片路徑')
    parser.add_argument('--output', '-o', default='.tmp/output/stickers', help='輸出目錄（預設：.tmp/output/stickers）')
    parser.add_argument('--rows', '-r', type=int, default=4, help='行數（預設：4）')
    parser.add_argument('--cols', '-c', type=int, default=5, help='列數（預設：5）')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("LINE 貼圖切割工具")
    print("=" * 60)
    
    # 驗證輸入圖片
    print("\n[1/3] 驗證輸入圖片...")
    is_valid, error_msg = validate_input_image(args.input)
    if not is_valid:
        print(f"✗ {error_msg}", file=sys.stderr)
        return 1
    print("✓ 輸入圖片驗證通過")
    
    # 切割圖片
    print(f"\n[2/3] 切割圖片...")
    count = split_image(args.input, args.output, args.rows, args.cols)
    if count == 0:
        print("✗ 切割失敗", file=sys.stderr)
        return 1
    
    # 完成
    print(f"\n[3/3] 完成")
    print("=" * 60)
    print(f"✓ 成功切割 {count} 張貼圖")
    print(f"✓ 輸出目錄：{Path(args.output).absolute()}")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
