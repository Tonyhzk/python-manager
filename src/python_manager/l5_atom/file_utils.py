# ==================== 文件操作工具 ====================
"""文件系统相关原子函数"""

import os
import shutil
import zipfile
from pathlib import Path
from typing import Optional


def locate_file(filepath: str) -> bool:
    """定位文件（macOS）"""
    if filepath and os.path.exists(filepath):
        import subprocess
        subprocess.run(["open", "-R", filepath])
        return True
    return False


def open_folder(folder: str) -> bool:
    """打开文件夹"""
    if folder and os.path.exists(folder):
        import subprocess
        subprocess.run(["open", folder])
        return True
    return False


def scan_python_files(directory: Path) -> list:
    """扫描目录下的Python文件"""
    return list(directory.glob("*.py"))


def copy_project_files(
    src_dir: str,
    dst_dir: str,
    ignore_patterns: Optional[tuple] = None
) -> bool:
    """复制项目文件，排除指定模式"""
    if ignore_patterns is None:
        ignore_patterns = ('venv', '.git', '__pycache__', '.idea', 'node_modules')
    try:
        shutil.copytree(src_dir, dst_dir, ignore=shutil.ignore_patterns(*ignore_patterns))
        return True
    except Exception:
        return False


def zip_folder(folder_path: str, output_path: str) -> bool:
    """压缩文件夹为ZIP"""
    try:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(folder_path))
                    zipf.write(file_path, arcname)
        return True
    except Exception:
        return False


def get_file_extension(filepath: str) -> str:
    """获取文件扩展名"""
    return Path(filepath).suffix.lower()


def is_image_file(filepath: str) -> bool:
    """检查是否为图片文件"""
    image_extensions = {'.ico', '.icns', '.png', '.jpg', '.jpeg', '.bmp', '.gif'}
    return get_file_extension(filepath) in image_extensions


def detect_icon_files(base_dir: Path) -> list:
    """自动检测图标文件"""
    icon_patterns = ["icon", "app_icon", "logo", "favicon"]
    icon_extensions = [".ico", ".icns", ".png"]

    detected = []
    for pattern in icon_patterns:
        for ext in icon_extensions:
            icon_path = base_dir / f"{pattern}{ext}"
            if icon_path.exists():
                detected.append(str(icon_path))
                break
    return detected


def write_file(filepath: str, content: str, encoding: str = "utf-8") -> bool:
    """写入文件内容"""
    try:
        with open(filepath, "w", encoding=encoding) as f:
            f.write(content)
        return True
    except Exception:
        return False


def copy_folder(src_dir: str, dst_dir: str, symlinks: bool = False, ignore_patterns: Optional[tuple] = None) -> bool:
    """复制整个文件夹（支持忽略模式和符号链接）"""
    if ignore_patterns is None:
        ignore_patterns = ('__pycache__', '*.pyc', '.git')
    try:
        shutil.copytree(
            src_dir,
            dst_dir,
            symlinks=symlinks,
            ignore=shutil.ignore_patterns(*ignore_patterns)
        )
        return True
    except Exception:
        return False
