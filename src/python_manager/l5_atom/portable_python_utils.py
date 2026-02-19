# ==================== 便携式Python打包工具 ====================
"""便携式Python环境打包 - 原子层纯函数"""

import os
import sys
import shutil
import subprocess
import zipfile
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Set, Callable, Dict


def clean_directory(directory: Path) -> None:
    """清理构建目录"""
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True, exist_ok=True)


def create_venv_portable(venv_path: Path, log_callback: Callable = None) -> bool:
    """创建虚拟环境（便携式）"""
    if log_callback:
        log_callback(f"创建虚拟环境: {venv_path}", "info")

    try:
        subprocess.run([
            sys.executable, "-m", "venv",
            str(venv_path),
            "--copies"  # 使用复制而不是符号链接，确保便携性
        ], check=True, capture_output=True)

        if log_callback:
            log_callback("虚拟环境创建成功！", "info")
        return True
    except Exception as e:
        if log_callback:
            log_callback(f"创建虚拟环境失败: {e}", "error")
        return False


def get_pip_path(venv_path: Path) -> Path:
    """获取虚拟环境中的pip路径"""
    if os.name == 'nt':  # Windows
        return venv_path / "Scripts" / "pip.exe"
    else:  # Linux/Mac
        return venv_path / "bin" / "pip"


def get_python_path(venv_path: Path) -> Path:
    """获取虚拟环境中的python路径"""
    if os.name == 'nt':  # Windows
        return venv_path / "Scripts" / "python.exe"
    else:  # Linux/Mac
        return venv_path / "bin" / "python"


def get_installed_packages() -> Dict[str, str]:
    """获取当前环境已安装的包列表"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=freeze"],
            capture_output=True,
            text=True,
            check=True,
            timeout=60
        )

        packages = {}
        for line in result.stdout.strip().split('\n'):
            if '==' in line:
                name, version = line.split('==')
                packages[name.lower()] = line

        return packages
    except Exception as e:
        return {}


def parse_requirements(requirements_file: Path) -> List[Tuple[str, str]]:
    """解析 requirements.txt 文件"""
    if not requirements_file.exists():
        return []

    required_packages = []
    try:
        with open(requirements_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                # 提取包名（去除版本号等）
                pkg_name = line.split('>=')[0].split('==')[0].split('<')[0].split('>')[0].strip()
                required_packages.append((pkg_name, line))
        return required_packages
    except Exception as e:
        return []


def get_package_dependencies(pkg_name: str) -> List[str]:
    """获取包的所有依赖"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", pkg_name],
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )

        for line in result.stdout.split('\n'):
            if line.startswith('Requires:'):
                deps = line.replace('Requires:', '').strip()
                if deps:
                    return [d.strip() for d in deps.split(',')]
        return []
    except Exception as e:
        return []


def copy_site_packages_from_env(
    venv_path: Path,
    package_names: Set[str],
    log_callback: Callable = None
) -> List[str]:
    """直接从当前环境的 site-packages 复制包到虚拟环境"""
    # 获取源和目标 site-packages 路径
    if os.name == 'nt':  # Windows
        src_site_packages = Path(sys.executable).parent / "Lib" / "site-packages"
        dst_site_packages = venv_path / "Lib" / "site-packages"
    else:  # Linux/Mac
        python_ver = f"python{sys.version_info.major}.{sys.version_info.minor}"
        src_site_packages = Path(sys.executable).parent.parent / "lib" / python_ver / "site-packages"
        dst_site_packages = venv_path / "lib" / python_ver / "site-packages"

    copied_packages = []

    for pkg_name in package_names:
        # 尝试多种可能的包目录名称
        possible_names = [
            pkg_name,
            pkg_name.lower(),
            pkg_name.replace('-', '_'),
            pkg_name.replace('_', '-'),
            pkg_name.lower().replace('-', '_'),
        ]

        copied = False
        for name in possible_names:
            # 查找包目录
            for item in src_site_packages.glob(f"{name}*"):
                if item.is_dir() and not item.name.endswith('.dist-info'):
                    # 复制包目录
                    dst = dst_site_packages / item.name
                    if not dst.exists():
                        try:
                            shutil.copytree(item, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                            if log_callback:
                                log_callback(f"  ✓ 复制包目录: {item.name}", "info")
                            copied = True
                        except Exception as e:
                            if log_callback:
                                log_callback(f"  ✗ 复制失败: {item.name}: {e}", "warning")
                elif item.is_file() and item.suffix == '.py':
                    # 复制单文件包
                    dst = dst_site_packages / item.name
                    if not dst.exists():
                        try:
                            shutil.copy2(item, dst)
                            if log_callback:
                                log_callback(f"  ✓ 复制包文件: {item.name}", "info")
                            copied = True
                        except Exception as e:
                            if log_callback:
                                log_callback(f"  ✗ 复制失败: {item.name}: {e}", "warning")

            # 查找 dist-info 目录
            for item in src_site_packages.glob(f"{name}*.dist-info"):
                dst = dst_site_packages / item.name
                if not dst.exists():
                    try:
                        shutil.copytree(item, dst)
                        if log_callback:
                            log_callback(f"  ✓ 复制元数据: {item.name}", "info")
                        copied = True
                    except Exception as e:
                        if log_callback:
                            log_callback(f"  ✗ 复制失败: {item.name}: {e}", "warning")

            if copied:
                copied_packages.append(pkg_name)
                break

    return copied_packages


def install_requirements_in_venv(
    pip_path: Path,
    requirements: List[str],
    log_callback: Callable = None
) -> Tuple[bool, int, int]:
    """在虚拟环境中安装依赖包

    返回: (成功标志, 成功数, 失败数)
    """
    success_count = 0
    fail_count = 0

    for req_spec in requirements:
        try:
            if log_callback:
                log_callback(f"下载安装: {req_spec}", "info")

            result = subprocess.run(
                [str(pip_path), "install", req_spec],
                capture_output=True,
                text=True,
                check=True,
                timeout=300
            )
            success_count += 1
            if log_callback:
                log_callback(f"  ✓ 安装成功", "info")
        except subprocess.TimeoutExpired:
            fail_count += 1
            if log_callback:
                log_callback(f"  ✗ 安装超时: {req_spec}", "error")
        except Exception as e:
            fail_count += 1
            if log_callback:
                log_callback(f"  ✗ 安装失败: {e}", "error")

    return (fail_count == 0, success_count, fail_count)


def get_site_packages_path(venv_path: Path) -> Path:
    """获取虚拟环境的site-packages路径"""
    if os.name == 'nt':  # Windows
        return venv_path / "Lib" / "site-packages"
    else:  # Linux/Mac
        python_ver = f"python{sys.version_info.major}.{sys.version_info.minor}"
        return venv_path / "lib" / python_ver / "site-packages"


def copy_project_files(
    src_dir: Path,
    dest_dir: Path,
    log_callback: Callable = None
) -> None:
    """复制项目文件"""
    if log_callback:
        log_callback(f"复制项目文件从 {src_dir}", "info")

    # 需要复制的项目结构
    items_to_copy = [
        "src",
        "scripts",
        "requirements.txt",
        "README.md",
        "pyproject.toml",
    ]

    # 忽略的文件和目录
    ignore_patterns = shutil.ignore_patterns(
        "__pycache__",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".git",
        ".gitignore",
        ".vscode",
        "build",
        "dist",
        ".pycache",
        "*.log",
        "logs",
        ".pytest_cache",
        ".tox",
        "*.egg-info",
    )

    for item in items_to_copy:
        src = src_dir / item
        if not src.exists():
            continue

        dest = dest_dir / item

        try:
            if src.is_dir():
                if log_callback:
                    log_callback(f"  复制目录: {item}", "info")
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(src, dest, ignore=ignore_patterns)
            elif src.is_file():
                if log_callback:
                    log_callback(f"  复制文件: {item}", "info")
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
        except Exception as e:
            if log_callback:
                log_callback(f"  ✗ 复制失败: {item}: {e}", "warning")


def create_launcher_scripts(
    build_dir: Path,
    app_name: str = "Application",
    log_callback: Callable = None
) -> None:
    """创建启动脚本"""
    if log_callback:
        log_callback("创建启动脚本", "info")

    # Windows 启动脚本
    windows_launcher = build_dir / f"启动 {app_name}.bat"
    windows_launcher.write_text(
        '@echo off\n'
        'chcp 65001 > nul\n'
        f'echo {"=" * 40}\n'
        f'echo {app_name} 启动中...\n'
        f'echo {"=" * 40}\n'
        'echo.\n'
        'cd /d "%~dp0"\n'
        f'set PYTHONPATH=%~dp0{app_name}\n'
        f'python_env\\Scripts\\python.exe {app_name}\\run.py\n'
        'pause\n',
        encoding='utf-8'
    )
    if log_callback:
        log_callback(f"创建 Windows 启动脚本: {windows_launcher.name}", "info")

    # Linux/Mac 启动脚本
    unix_launcher = build_dir / f"启动_{app_name}.sh"
    unix_launcher.write_text(
        '#!/bin/bash\n'
        f'echo "{"=" * 40}"\n'
        f'echo "{app_name} 启动中..."\n'
        f'echo "{"=" * 40}"\n'
        'echo ""\n'
        'cd "$(dirname "$0")"\n'
        f'export PYTHONPATH="$(pwd)/{app_name}"\n'
        f'./python_env/bin/python {app_name}/run.py\n',
        encoding='utf-8'
    )
    unix_launcher.chmod(0o755)
    if log_callback:
        log_callback(f"创建 Unix 启动脚本: {unix_launcher.name}", "info")


def create_readme(build_dir: Path, python_version: str, app_name: str = "Application") -> None:
    """创建 README 文件"""
    readme = build_dir / "README.txt"
    readme_content = (
        f'{app_name} - 便携式 Python 环境\n'
        '=' * 60 + '\n\n'
        f'Python 版本: {python_version}\n'
        f'打包时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n'
        '使用说明:\n'
        '-' * 60 + '\n'
        'Windows 用户:\n'
        f'  双击运行 "启动 {app_name}.bat"\n\n'
        'Linux/Mac 用户:\n'
        f'  在终端中运行: ./启动_{app_name}.sh\n\n'
        '目录结构:\n'
        '-' * 60 + '\n'
        'python_env/          - Python 虚拟环境\n'
        f'{app_name}/        - 项目源代码\n'
        f'启动 {app_name}.bat  - Windows 启动脚本\n'
        f'启动_{app_name}.sh   - Unix 启动脚本\n\n'
        '注意事项:\n'
        '-' * 60 + '\n'
        '1. 请勿删除或移动 python_env 目录\n'
        '2. 整个文件夹可以复制到其他位置使用\n'
        '3. 如需更新依赖，请在 python_env 中使用 pip\n'
    )
    readme.write_text(readme_content, encoding='utf-8')


def create_zip_archive(
    build_dir: Path,
    output_dir: Path,
    output_filename: str,
    log_callback: Callable = None
) -> Path:
    """创建 ZIP 压缩包"""
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / output_filename

    if log_callback:
        log_callback(f"压缩目标: {output_path}", "info")
        log_callback("压缩中，请稍候...", "info")

    try:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            count = 0
            for root, dirs, files in os.walk(build_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(build_dir)
                    zipf.write(file_path, arcname)
                    count += 1

                    # 显示进度
                    if count % 100 == 0 and log_callback:
                        log_callback(f"  已压缩 {count} 个文件...", "info")

        file_size = output_path.stat().st_size / (1024 * 1024)  # MB
        if log_callback:
            log_callback(f"✓ 压缩完成！文件大小: {file_size:.2f} MB", "info")

        return output_path
    except Exception as e:
        if log_callback:
            log_callback(f"✗ 压缩失败: {e}", "error")
        raise


def generate_output_filename(
    python_version: str,
    app_name: str = "Application"
) -> str:
    """生成输出文件名"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{app_name}_Python_{python_version}_{timestamp}.zip"
