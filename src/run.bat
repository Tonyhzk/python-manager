@echo off
REM GUI启动脚本

REM 获取脚本所在目录（程序根目录）
set SCRIPT_DIR=%~dp0

REM 项目目录（程序根目录的父目录）
set PROJECT_ROOT=%SCRIPT_DIR%..

REM 设置 PYTHONPYCACHEPREFIX 环境变量（统一管理.pycache）
set PYTHONPYCACHEPREFIX=%SCRIPT_DIR%.pycache

REM 检测并激活虚拟环境（先检测项目目录，再检测程序根目录）
if exist "%PROJECT_ROOT%\.venv\Scripts\activate.bat" (
    call "%PROJECT_ROOT%\.venv\Scripts\activate.bat"
    echo [已激活虚拟环境：项目目录]
) else if exist "%SCRIPT_DIR%.venv\Scripts\activate.bat" (
    call "%SCRIPT_DIR%.venv\Scripts\activate.bat"
    echo [已激活虚拟环境：程序根目录]
) else (
    echo [未检测到虚拟环境，使用系统Python]
)

REM 启动GUI应用
python "%SCRIPT_DIR%run.py" %*
