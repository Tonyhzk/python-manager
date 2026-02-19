# ==================== 克隆管理器 ====================
"""Python环境克隆业务逻辑管理器"""

import os
import platform
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Optional

from l5_atom import (
    copy_project_files,
    zip_folder,
    create_venv,
    pip_install_in_venv,
    run_command,
    copy_folder,
    write_file,
)


class CloneManager:
    """环境克隆管理器"""

    def get_python_prefix(self, python_path: str) -> str:
        """获取Python安装前缀"""
        try:
            result = run_command(
                [python_path, "-c", "import sys; print(sys.prefix)"],
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return os.path.dirname(os.path.dirname(python_path))

    def clone_full_environment(
        self,
        python_path: str,
        target_dir: str,
        log_callback: Callable[[str, str], None]
    ) -> bool:
        """完整克隆Python环境"""
        try:
            python_root = self.get_python_prefix(python_path)
            log_callback(f"原始安装路径: {python_root}", "info")

            env_dest = os.path.join(target_dir, "python_env")
            log_callback("开始克隆Python环境文件...", "info")

            success = copy_folder(
                python_root,
                env_dest,
                symlinks=True,
                ignore_patterns=('__pycache__', '*.pyc', '.git')
            )
            if success:
                log_callback("环境克隆完成", "success")
                return True
            else:
                log_callback("克隆失败", "error")
                return False
        except Exception as e:
            log_callback(f"克隆失败: {e}", "error")
            return False

    def clone_clean_environment(
        self,
        python_path: str,
        target_dir: str,
        project_dir: str,
        include_project: bool,
        stdlib_modules: set,
        log_callback: Callable[[str, str], None]
    ) -> bool:
        """纯净克隆Python环境（创建venv）"""
        log_callback("开始创建纯净venv环境...", "info")

        venv_dest = os.path.join(target_dir, "venv")

        try:
            # 创建venv
            log_callback(f"执行: {python_path} -m venv {venv_dest}", "info")
            success = create_venv(python_path, venv_dest)
            if not success:
                log_callback("创建venv失败", "error")
                return False
            log_callback("venv环境创建成功", "success")

            # 获取venv中的python路径
            if platform.system() == "Windows":
                venv_python = os.path.join(venv_dest, "Scripts", "python.exe")
            else:
                venv_python = os.path.join(venv_dest, "bin", "python")

            # 复制项目源码
            if include_project and project_dir:
                log_callback("正在复制项目源码...", "info")
                src_dest = os.path.join(target_dir, "project_src")
                success = copy_project_files(project_dir, src_dest)
                if success:
                    log_callback("源码复制完成", "success")

                    # 分析项目依赖
                    log_callback("正在分析项目依赖...", "info")
                    from l5_atom import analyze_project_directory
                    deps = analyze_project_directory(project_dir, stdlib_modules)

                    if deps:
                        log_callback(f"发现 {len(deps)} 个依赖，开始安装...", "info")
                        for dep in deps:
                            log_callback(f"  安装 {dep}...", "info")
                            pip_install_in_venv(venv_python, dep)
                        log_callback("依赖安装完成", "success")
                    else:
                        log_callback("未发现外部依赖", "info")

            # 生成requirements.txt
            log_callback("生成依赖列表...", "info")
            from l5_atom import freeze_requirements
            req_file = os.path.join(target_dir, "requirements.txt")
            freeze_requirements(venv_python, req_file)
            log_callback("依赖列表已保存", "success")

            return True

        except Exception as e:
            log_callback(f"错误: {e}", "error")
            return False

    def download_dependencies(
        self,
        python_path: str,
        target_dir: str,
        log_callback: Callable[[str, str], None]
    ) -> bool:
        """下载依赖包"""
        packages_dir = os.path.join(target_dir, "packages")
        os.makedirs(packages_dir, exist_ok=True)

        # 生成requirements.txt
        log_callback("生成依赖列表...", "info")
        from l5_atom import freeze_requirements, download_requirements
        req_file = os.path.join(target_dir, "requirements.txt")
        freeze_requirements(python_path, req_file)

        # 下载依赖
        log_callback("下载依赖包...", "info")
        success = download_requirements(req_file, packages_dir, python_path)
        if success:
            log_callback("依赖下载完成", "success")
        return success

    def create_start_scripts(
        self,
        target_dir: str,
        include_project: bool,
        log_callback: Callable[[str, str], None]
    ) -> None:
        """生成启动脚本"""
        cd_cmd = f'cd /d "{os.path.join(target_dir, "project_src")}"' if include_project else 'REM No project'

        # Windows启动脚本
        bat_content = f"""@echo off
set "CURRENT_DIR=%~dp0"
set "PYTHON_HOME=%CURRENT_DIR%python_env"
set "PROJECT_DIR=%CURRENT_DIR%project_src"

echo [INFO] Setting up environment...
set "PATH=%PYTHON_HOME%;%PYTHON_HOME%\\Scripts;%PATH%"

python --version
echo [INFO] Ready!
echo.
{cd_cmd}
cmd /k
"""
        bat_path = os.path.join(target_dir, "Start_Console_Portable.bat")
        write_file(bat_path, bat_content, encoding="gbk")
        log_callback("已生成启动脚本", "success")

    def execute_clone(
        self,
        mode: int,
        project_dir: str,
        output_dir: str,
        python_path: str,
        include_project: bool,
        compress_zip: bool,
        stdlib_modules: set,
        log_callback: Callable[[str, str], None]
    ) -> tuple:
        """执行环境克隆主流程"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if mode == 2:
            pack_name = f"PyClone_Full_{timestamp}"
        elif mode == 3:
            pack_name = f"PyClone_Clean_{timestamp}"
        else:
            pack_name = f"PyPack_{timestamp}"

        target_dir = os.path.join(output_dir, pack_name)
        os.makedirs(target_dir, exist_ok=True)

        success = False
        if mode == 2:
            success = self.clone_full_environment(python_path, target_dir, log_callback)
            if success and include_project and project_dir:
                log_callback("正在复制项目源码...", "info")
                src_dest = os.path.join(target_dir, "project_src")
                copy_project_files(project_dir, src_dest)
                log_callback("源码复制完成", "success")
            self.create_start_scripts(target_dir, include_project, log_callback)

        elif mode == 3:
            success = self.clone_clean_environment(
                python_path, target_dir, project_dir, include_project, stdlib_modules, log_callback
            )

        else:
            success = self.download_dependencies(python_path, target_dir, log_callback)
            if success and include_project and project_dir:
                log_callback("正在复制项目源码...", "info")
                src_dest = os.path.join(target_dir, "project_src")
                copy_project_files(project_dir, src_dest)
                log_callback("源码复制完成", "success")

        # 压缩
        if success and compress_zip:
            log_callback("正在生成ZIP压缩包...", "info")
            zip_path = os.path.join(output_dir, f"{pack_name}.zip")
            if zip_folder(target_dir, zip_path):
                log_callback(f"打包完成: {zip_path}", "success")

        return success, target_dir
