#!/usr/bin/env python3
"""
System Health Check Script
驗證 Agent 系統所有組件是否正常運作
"""

import sys
from pathlib import Path

def check_file_exists(file_path, description):
    """檢查文件是否存在"""
    if Path(file_path).exists():
        print(f"✓ {description}")
        return True
    else:
        print(f"✗ {description} - 文件不存在: {file_path}")
        return False

def check_directory_exists(dir_path, description):
    """檢查目錄是否存在"""
    if Path(dir_path).is_dir():
        print(f"✓ {description}")
        return True
    else:
        print(f"✗ {description} - 目錄不存在: {dir_path}")
        return False

def check_python_import(module_name):
    """檢查 Python 模組是否可以導入"""
    try:
        __import__(module_name)
        print(f"✓ Python 模組: {module_name}")
        return True
    except ImportError:
        print(f"✗ Python 模組缺失: {module_name} (運行 pip install -r requirements.txt)")
        return False

def main():
    print("=" * 60)
    print("Agent 系統健康檢查")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    checks_passed = 0
    total_checks = 0
    
    # 檢查文檔
    print("\n[1/6] 檢查文檔文件...")
    docs = [
        (base_dir / "README.md", "README.md"),
        (base_dir / "QUICKSTART.md", "QUICKSTART.md"),
        (base_dir / "ARCHITECTURE.md", "ARCHITECTURE.md"),
        (base_dir / "GETTING_STARTED.md", "GETTING_STARTED.md"),
        (base_dir / "agent.md", "agent.md"),
    ]
    for path, desc in docs:
        total_checks += 1
        if check_file_exists(path, desc):
            checks_passed += 1
    
    # 檢查目錄結構
    print("\n[2/6] 檢查目錄結構...")
    dirs = [
        (base_dir / "directives", "directives/"),
        (base_dir / "execution", "execution/"),
        (base_dir / "execution" / "utils", "execution/utils/"),
        (base_dir / ".tmp", ".tmp/"),
        (base_dir / ".tmp" / "input", ".tmp/input/"),
        (base_dir / ".tmp" / "output", ".tmp/output/"),
        (base_dir / ".tmp" / "logs", ".tmp/logs/"),
    ]
    for path, desc in dirs:
        total_checks += 1
        if check_directory_exists(path, desc):
            checks_passed += 1
    
    # 檢查指令文件
    print("\n[3/6] 檢查指令文件...")
    directives = [
        (base_dir / "directives" / "README.md", "directives/README.md"),
        (base_dir / "directives" / "example_directive.md", "directives/example_directive.md"),
    ]
    for path, desc in directives:
        total_checks += 1
        if check_file_exists(path, desc):
            checks_passed += 1
    
    # 檢查執行腳本
    print("\n[4/6] 檢查執行腳本...")
    scripts = [
        (base_dir / "execution" / "README.md", "execution/README.md"),
        (base_dir / "execution" / "agent_orchestrator.py", "agent_orchestrator.py"),
        (base_dir / "execution" / "split_stickers.py", "split_stickers.py"),
        (base_dir / "execution" / "example_script.py", "example_script.py"),
        (base_dir / "execution" / "utils" / "__init__.py", "utils/__init__.py"),
        (base_dir / "execution" / "utils" / "logger.py", "utils/logger.py"),
    ]
    for path, desc in scripts:
        total_checks += 1
        if check_file_exists(path, desc):
            checks_passed += 1
    
    # 檢查配置文件
    print("\n[5/6] 檢查配置文件...")
    configs = [
        (base_dir / ".env.example", ".env.example"),
        (base_dir / ".gitignore", ".gitignore"),
        (base_dir / "requirements.txt", "requirements.txt"),
    ]
    for path, desc in configs:
        total_checks += 1
        if check_file_exists(path, desc):
            checks_passed += 1
    
    # 檢查 Python 依賴（可選）
    print("\n[6/6] 檢查 Python 依賴（可選）...")
    print("（如果缺少，請運行: pip install -r requirements.txt）")
    modules = ["PIL", "dotenv"]  # 核心依賴
    for module in modules:
        total_checks += 1
        if check_python_import(module):
            checks_passed += 1
    
    # 總結
    print("\n" + "=" * 60)
    print(f"檢查完成: {checks_passed}/{total_checks} 項通過")
    print("=" * 60)
    
    if checks_passed == total_checks:
        print("✓ 系統健康狀態良好！所有組件都已就緒。")
        print("\n下一步：")
        print("1. 運行: pip install -r requirements.txt")
        print("2. 閱讀: GETTING_STARTED.md")
        print("3. 試用: python execution\\split_stickers.py --help")
        return 0
    else:
        print(f"⚠ 發現 {total_checks - checks_passed} 個問題，請檢查上述輸出。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
