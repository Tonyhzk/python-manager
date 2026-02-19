#!/bin/bash
# GUI启动脚本

# 获取脚本所在目录（程序根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 项目目录（程序根目录的父目录）
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 设置 PYTHONPYCACHEPREFIX 环境变量（统一管理.pycache）
export PYTHONPYCACHEPREFIX="$SCRIPT_DIR/.pycache"

# 检测并激活虚拟环境（先检测项目目录，再检测程序根目录）
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
    echo "[已激活虚拟环境：项目目录]"
elif [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
    echo "[已激活虚拟环境：程序根目录]"
else
    echo "[未检测到虚拟环境，使用系统Python]"
fi

# 启动GUI应用
python3 "$SCRIPT_DIR/run.py" "$@"
