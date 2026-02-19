#!/usr/bin/env python3
"""
GUI启动入口
"""

import os
import sys
from pathlib import Path

# 获取脚本所在目录（程序根目录）
SCRIPT_DIR = Path(__file__).parent.resolve()

# 项目目录（程序根目录的父目录）
PROJECT_ROOT = SCRIPT_DIR.parent

# 设置 PYTHONPYCACHEPREFIX 环境变量（统一管理.pycache）
pycache_dir = SCRIPT_DIR / ".pycache"
os.environ["PYTHONPYCACHEPREFIX"] = str(pycache_dir)

# 添加 src 目录到 Python 路径
src_dir = SCRIPT_DIR / "src" / "python_manager"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# 检测虚拟环境（提示信息，实际激活由.bat/.sh完成）
project_venv = PROJECT_ROOT / ".venv"
local_venv = SCRIPT_DIR / ".venv"

if project_venv.exists():
    print("[检测到虚拟环境：项目目录]")
elif local_venv.exists():
    print("[检测到虚拟环境：程序根目录]")
else:
    print("[未检测到虚拟环境，使用系统Python]")

# 启动GUI应用
if __name__ == "__main__":
    from l1_entry import main_gui
    main_gui()
