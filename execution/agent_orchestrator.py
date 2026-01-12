#!/usr/bin/env python3
"""
Script Name: agent_orchestrator.py
Purpose: Agent 系統的主要編排器 - 負責讀取指令並協調執行腳本
Author: Agent System
Created: 2026-01-11

這個腳本作為 Agent 系統的第二層（編排層），負責：
1. 讀取 directives/ 中的指令
2. 解析任務需求
3. 按順序調用 execution/ 中的執行腳本
4. 處理錯誤和異常
5. 記錄執行過程
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import json

# 添加 utils 到路徑
sys.path.insert(0, str(Path(__file__).parent))
from utils.logger import setup_logger

logger = setup_logger('orchestrator', '.tmp/logs/orchestrator.log')

class AgentOrchestrator:
    """
    Agent 編排器
    """
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.directives_dir = base_dir / 'directives'
        self.execution_dir = base_dir / 'execution'
        self.tmp_dir = base_dir / '.tmp'
        
    def list_directives(self) -> List[str]:
        """
        列出所有可用的指令
        """
        if not self.directives_dir.exists():
            logger.warning(f"指令目錄不存在：{self.directives_dir}")
            return []
        
        directives = []
        for file in self.directives_dir.glob('*.md'):
            if file.name != 'README.md':
                directives.append(file.stem)
        
        return sorted(directives)
    
    def read_directive(self, name: str) -> Optional[str]:
        """
        讀取指令內容
        """
        directive_path = self.directives_dir / f"{name}.md"
        if not directive_path.exists():
            logger.error(f"指令檔案不存在：{directive_path}")
            return None
        
        try:
            with open(directive_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"讀取指令失敗：{e}")
            return None
    
    def execute_script(self, script_name: str, args: List[str]) -> Dict:
        """
        執行指定的 Python 腳本
        
        Args:
            script_name: 腳本名稱（不含 .py）
            args: 腳本參數列表
            
        Returns:
            Dict: 執行結果 {'success': bool, 'output': str, 'error': str}
        """
        script_path = self.execution_dir / f"{script_name}.py"
        
        if not script_path.exists():
            return {
                'success': False,
                'output': '',
                'error': f'腳本不存在：{script_path}'
            }
        
        try:
            cmd = [sys.executable, str(script_path)] + args
            logger.info(f"執行命令：{' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=300  # 5分鐘超時
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr,
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': '執行逾時（超過 5 分鐘）'
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'執行異常：{str(e)}'
            }
    
    def run_sticker_split_task(self, input_image: str, output_dir: str = None, 
                               rows: int = 4, cols: int = 5) -> bool:
        """
        執行貼圖切割任務
        
        這是一個預定義的任務流程，展示如何編排多個步驟
        """
        logger.info("=" * 60)
        logger.info("開始執行：LINE 貼圖切割任務")
        logger.info("=" * 60)
        
        if output_dir is None:
            output_dir = str(self.tmp_dir / 'output' / 'stickers')
        
        # 步驟 1: 執行切割
        logger.info("\n[步驟 1] 執行圖片切割...")
        args = [
            '--input', input_image,
            '--output', output_dir,
            '--rows', str(rows),
            '--cols', str(cols)
        ]
        
        result = self.execute_script('split_stickers', args)
        
        if not result['success']:
            logger.error(f"切割失敗：{result['error']}")
            return False
        
        logger.info(result['output'])
        
        # 未來可以添加更多步驟，例如：
        # 步驟 2: 驗證輸出
        # 步驟 3: 壓縮優化
        # 步驟 4: 上傳到雲端
        
        logger.info("=" * 60)
        logger.info("✓ 任務完成")
        logger.info("=" * 60)
        
        return True

def main():
    parser = argparse.ArgumentParser(
        description='Agent 系統編排器 - 協調指令和執行腳本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例用法:
  # 列出所有可用指令
  python agent_orchestrator.py --list

  # 查看特定指令
  python agent_orchestrator.py --show example_directive

  # 執行貼圖切割任務
  python agent_orchestrator.py --task split-stickers --input image.png

  # 執行自訂腳本
  python agent_orchestrator.py --script split_stickers --args "--input image.png --output out"
        """
    )
    
    parser.add_argument('--list', '-l', action='store_true',
                       help='列出所有可用的指令')
    parser.add_argument('--show', '-s', metavar='NAME',
                       help='顯示指定指令的內容')
    parser.add_argument('--task', '-t', metavar='TASK',
                       help='執行預定義任務（例如：split-stickers）')
    parser.add_argument('--input', '-i', metavar='PATH',
                       help='任務輸入檔案路徑')
    parser.add_argument('--output', '-o', metavar='PATH',
                       help='任務輸出目錄路徑')
    parser.add_argument('--script', metavar='NAME',
                       help='直接執行指定的執行腳本')
    parser.add_argument('--args', metavar='ARGS',
                       help='傳遞給腳本的參數（用引號包裹）')
    
    args = parser.parse_args()
    
    # 初始化編排器
    base_dir = Path(__file__).parent.parent
    orchestrator = AgentOrchestrator(base_dir)
    
    # 列出指令
    if args.list:
        print("\n📋 可用指令：")
        print("=" * 60)
        directives = orchestrator.list_directives()
        if directives:
            for d in directives:
                print(f"  • {d}")
        else:
            print("  （無可用指令）")
        print("=" * 60)
        return 0
    
    # 顯示指令內容
    if args.show:
        print(f"\n📄 指令：{args.show}")
        print("=" * 60)
        content = orchestrator.read_directive(args.show)
        if content:
            print(content)
        print("=" * 60)
        return 0
    
    # 執行預定義任務
    if args.task:
        if args.task == 'split-stickers':
            if not args.input:
                print("錯誤：請使用 --input 指定輸入圖片", file=sys.stderr)
                return 1
            
            success = orchestrator.run_sticker_split_task(
                input_image=args.input,
                output_dir=args.output
            )
            return 0 if success else 1
        else:
            print(f"錯誤：未知任務 '{args.task}'", file=sys.stderr)
            return 1
    
    # 直接執行腳本
    if args.script:
        script_args = []
        if args.args:
            # 簡單的參數分割（可以改進）
            script_args = args.args.split()
        
        result = orchestrator.execute_script(args.script, script_args)
        
        if result['output']:
            print(result['output'])
        if result['error']:
            print(result['error'], file=sys.stderr)
        
        return 0 if result['success'] else 1
    
    # 如果沒有指定任何操作，顯示幫助
    parser.print_help()
    return 0

if __name__ == "__main__":
    sys.exit(main())
