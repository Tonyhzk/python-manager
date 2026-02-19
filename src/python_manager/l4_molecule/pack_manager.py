# ==================== 打包管理器 ====================
"""PyInstaller打包业务逻辑管理器"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Callable, Dict, Optional

from l5_atom import (
    check_pyinstaller_installed,
    detect_icon_files,
    run_command,
    run_process_with_callback,
)


class PackManager:
    """PyInstaller打包管理器"""

    def __init__(self):
        self.stdlib_modules = None

    def set_stdlib_modules(self, modules: set):
        """设置标准库模块集合"""
        self.stdlib_modules = modules

    def check_pyinstaller(self, python_path: str = "pyinstaller") -> tuple:
        """检查PyInstaller状态"""
        return check_pyinstaller_installed(python_path)

    def install_pyinstaller(self, python_path: str = sys.executable) -> bool:
        """安装PyInstaller"""
        result = run_command(
            [python_path, "-m", "pip", "install", "pyinstaller"],
            capture_output=True
        )
        return result.returncode == 0

    def detect_icons(self, py_file: str, resource_folder: str = "") -> list:
        """自动检测图标文件"""
        py_path = Path(py_file)
        base_dir = py_path.parent
        search_dirs = [base_dir]

        if resource_folder:
            res_path = Path(resource_folder)
            if res_path.exists() and res_path.is_dir():
                search_dirs.append(res_path)

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            icons = detect_icon_files(search_dir)
            if icons:
                return icons
        return []

    def build_command(
        self,
        py_file: str,
        output_folder: str,
        options: Dict
    ) -> tuple:
        """构建PyInstaller命令"""
        import os

        cmd = ["pyinstaller"]

        if options.get("onefile"):
            cmd.append("--onefile")
        else:
            cmd.append("--onedir")

        if options.get("windowed") and not options.get("console"):
            cmd.append("--windowed")
        elif options.get("console"):
            cmd.append("--console")

        cmd.append("--noconfirm")

        py_path = Path(py_file)
        script_dir = str(py_path.parent)
        build_path = tempfile.gettempdir()

        # 按原始逻辑处理输出目录
        if output_folder:
            # 如果是目录而非 dist 文件夹，自动追加 /dist
            if os.path.isdir(output_folder):
                dist_path = os.path.join(output_folder, "dist")
            else:
                dist_path = output_folder
        else:
            # 默认输出到脚本所在目录的 dist
            dist_path = os.path.join(script_dir, "dist")

        cmd.extend(["--distpath", dist_path])
        cmd.extend(["--workpath", build_path])
        cmd.extend(["--specpath", script_dir])

        if options.get("icon"):
            cmd.extend(["--icon", options["icon"]])

        if options.get("resource_folder"):
            cmd.extend(["--add-data", f"{options['resource_folder']};."])

        cmd.append(py_file)
        return cmd, dist_path

    def run_pack(
        self,
        py_file: str,
        output_folder: str,
        options: Dict,
        log_callback: Callable[[str, str], None]
    ) -> tuple:
        """执行打包"""
        cmd, dist_path = self.build_command(py_file, output_folder, options)

        log_callback(f"执行命令: {' '.join(cmd)}", "info")
        log_callback(f"输出目录: {dist_path}", "info")

        def line_callback(line: str):
            log_callback(line, "info")

        returncode = run_process_with_callback(cmd, line_callback)

        if returncode == 0:
            log_callback("打包成功!", "success")
            return True, dist_path
        else:
            log_callback("打包失败", "error")
            return False, ""
