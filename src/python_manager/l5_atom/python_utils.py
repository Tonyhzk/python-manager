# ==================== Python版本检测工具 ====================
"""Python解释器版本检测相关原子函数"""

import subprocess
import sys
import platform
from pathlib import Path
from typing import Dict, List, Optional


def get_stdlib_modules() -> set:
    """获取Python标准库模块集合"""
    return {
        'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio',
        'asyncore', 'atexit', 'audioop', 'base64', 'binascii', 'binhex',
        'bisect', 'builtins', 'bz2', 'calendar', 'cgi', 'cgitb', 'chunk',
        'cmath', 'cmd', 'code', 'codecs', 'codeop', 'collections',
        'colorsys', 'compileall', 'concurrent', 'configparser', 'contextlib',
        'contextvars', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv', 'ctypes',
        'curses', 'dataclasses', 'decimal', 'difflib', 'dis', 'distutils',
        'doctest', 'email', 'encodings', 'enum', 'errno', 'faulthandler',
        'fcntl', 'filecmp', 'fileinput', 'fnmatch', 'formatter', 'fractions',
        'ftplib', 'functools', 'gc', 'getopt', 'getpass', 'gettext', 'glob',
        'grp', 'gzip', 'hashlib', 'heapq', 'hmac', 'html', 'http', 'imaplib',
        'imghdr', 'imp', 'importlib', 'inspect', 'io', 'ipaddress', 'itertools',
        'json', 'keyword', 'lib2to3', 'linecache', 'locale', 'logging', 'lzma',
        'mailbox', 'mailcap', 'marshal', 'math', 'mimetypes', 'mmap',
        'modulefinder', 'msilib', 'msvcrt', 'multiprocessing', 'netrc', 'nis',
        'nntplib', 'numbers', 'operator', 'optparse', 'os', 'ossaudiodev',
        'parser', 'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil',
        'platform', 'plistlib', 'poplib', 'posix', 'posixpath', 'pprint',
        'profile', 'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc',
        'queue', 'quopri', 'random', 're', 'readline', 'reprlib', 'resource',
        'rlcompleter', 'runpy', 'sched', 'secrets', 'select', 'selectors',
        'shelve', 'shlex', 'shutil', 'signal', 'site', 'smtpd', 'smtplib',
        'sndhdr', 'socket', 'socketserver', 'spwd', 'sqlite3', 'ssl', 'stat',
        'statistics', 'string', 'stringprep', 'struct', 'subprocess', 'sunau',
        'symbol', 'symtable', 'sys', 'sysconfig', 'syslog', 'tabnanny',
        'tarfile', 'telnetlib', 'tempfile', 'termios', 'test', 'textwrap',
        'threading', 'time', 'timeit', 'tkinter', 'token', 'tokenize', 'trace',
        'traceback', 'tracemalloc', 'tty', 'turtle', 'types', 'typing',
        'unicodedata', 'unittest', 'urllib', 'uu', 'uuid', 'venv', 'warnings',
        'wave', 'weakref', 'webbrowser', 'winreg', 'winsound', 'wsgiref',
        'xdrlib', 'xml', 'xmlrpc', 'zipapp', 'zipfile', 'zipimport', 'zlib'
    }


def is_stdlib_module(module_name: str) -> bool:
    """检查模块是否属于标准库"""
    return module_name.lower() in get_stdlib_modules()


def get_python_info(python_path: str) -> Optional[Dict]:
    """获取Python解释器的详细信息"""
    try:
        cmd = [
            python_path,
            "-c",
            "import sys; print(sys.executable); print(sys.version); print(sys.prefix)"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            return None

        lines = result.stdout.strip().split('\n')
        if len(lines) < 3:
            return None

        version = lines[1].split()[0]
        version_parts = version.split('.')
        major_minor = f"{version_parts[0]}.{version_parts[1]}"
        version_tuple = (
            int(version_parts[0]),
            int(version_parts[1]),
            int(version_parts[2]) if len(version_parts) > 2 else 0
        )

        prefix = lines[2].strip() if len(lines) > 2 else lines[0].strip()

        # 获取编译信息
        compile_info = ""
        try:
            cmd2 = [
                python_path,
                "-c",
                "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX') or '.so')"
            ]
            result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=5)
            compile_info = result2.stdout.strip()
        except Exception:
            pass

        return {
            "path": python_path,
            "version": version,
            "version_tuple": version_tuple,
            "major_minor": major_minor,
            "prefix": prefix,
            "compile_suffix": compile_info,
            "is_current": python_path == sys.executable
        }
    except Exception:
        return None


def detect_python_versions() -> List[Dict]:
    """使用where/which命令检测系统中安装的所有Python版本"""
    python_list = []
    system = platform.system()

    # 1. 检测当前运行的Python
    current_info = get_python_info(sys.executable)
    if current_info:
        python_list.append(current_info)

    # 2. 使用where/which命令查找Python
    if system == "Windows":
        try:
            result = subprocess.run(
                ["where", "python*"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    path = line.strip()
                    if path and path != sys.executable:
                        info = get_python_info(path)
                        if info:
                            python_list.append(info)
        except Exception:
            pass
    else:
        for version in [
            "python3.12", "python3.11", "python3.10",
            "python3.9", "python3"
        ]:
            try:
                result = subprocess.run(
                    ["which", version],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    path = result.stdout.strip()
                    if path and path != sys.executable:
                        info = get_python_info(path)
                        if info and info["path"] not in [p["path"] for p in python_list]:
                            python_list.append(info)
            except Exception:
                pass

    # 3. 从PATH环境变量检测
    import os as _os
    path_env = _os.environ.get("PATH", "")
    for path_entry in path_env.split(_os.pathsep):
        p = Path(path_entry)
        if p.exists():
            for py_name in ["python", "python3"]:
                py_exe = p / py_name
                if py_exe.exists() and py_exe.suffix == "":
                    info = get_python_info(str(py_exe))
                    if info and info["path"] not in [p["path"] for p in python_list]:
                        python_list.append(info)

    # 4. pyenv检测（macOS/Linux）
    if system != "Windows":
        try:
            result = subprocess.run(
                ["pyenv", "versions", "--skip-env"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.strip() and not line.strip().startswith('*'):
                        version = line.strip()
                        pyenv_path = (
                            Path.home() / ".pyenv" / "versions" /
                            version / "bin" / "python"
                        )
                        if pyenv_path.exists():
                            info = get_python_info(str(pyenv_path))
                            if info and info["path"] not in [p["path"] for p in python_list]:
                                info["source"] = "pyenv"
                                python_list.append(info)
        except Exception:
            pass

    # 去重并按版本号降序排序
    seen = set()
    unique = []
    for p in python_list:
        if p["path"] not in seen:
            seen.add(p["path"])
            unique.append(p)

    unique.sort(key=lambda x: x["version_tuple"], reverse=True)
    return unique


def check_pyinstaller_installed(python_path: str = "pyinstaller") -> tuple:
    """检查PyInstaller是否已安装，返回(是否安装, 版本号)"""
    try:
        result = subprocess.run(
            [python_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
    except Exception:
        pass
    return False, ""


def check_module_installed(module_name: str, python_path: str = sys.executable) -> bool:
    """检查模块是否已安装"""
    try:
        result = subprocess.run(
            [python_path, "-c", f"import {module_name}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False
