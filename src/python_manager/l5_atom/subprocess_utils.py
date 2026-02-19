# ==================== 子进程工具 ====================
"""子进程执行相关原子函数"""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List, Callable, Tuple


def run_command(
    cmd: List[str],
    timeout: Optional[int] = None,
    capture_output: bool = True,
    env: Optional[dict] = None
) -> subprocess.CompletedProcess:
    """执行命令并返回结果"""
    return subprocess.run(
        cmd,
        timeout=timeout,
        capture_output=capture_output,
        text=True,
        env=env
    )


def run_command_iter(
    cmd: List[str],
    line_callback: Callable[[str], None],
    timeout: Optional[int] = None,
    env: Optional[dict] = None
) -> int:
    """执行命令，逐行回调输出"""
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env
    )

    for line in process.stdout:
        line_callback(line.strip())

    process.wait()
    return process.returncode


def run_command_capture(
    cmd: List[str],
    timeout: Optional[int] = None,
    cwd: Optional[str] = None,
    shell: bool = False
) -> Tuple[int, str, str]:
    """执行命令，返回(返回码, stdout, stderr)"""
    try:
        result = subprocess.run(
            cmd,
            timeout=timeout,
            capture_output=True,
            text=True,
            cwd=cwd,
            shell=shell
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except Exception as e:
        return -1, "", str(e)


def create_venv(python_path: str, venv_path: str) -> bool:
    """创建虚拟环境"""
    try:
        result = subprocess.run(
            [python_path, "-m", "venv", venv_path],
            timeout=120,
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def pip_install_in_venv(
    venv_python: str,
    package: str,
    timeout: int = 120
) -> bool:
    """在虚拟环境中安装包"""
    try:
        result = subprocess.run(
            [venv_python, "-m", "pip", "install", package],
            timeout=timeout,
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def run_process_with_callback(
    cmd: List[str],
    line_callback: Callable[[str], None],
    timeout: Optional[int] = None
) -> int:
    """执行进程并逐行回调 (用于PyInstaller等长时间运行任务)"""
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        try:
            for line in process.stdout:
                if line.strip():
                    line_callback(line.strip())
        except Exception:
            pass
        finally:
            process.wait(timeout=timeout)

        return process.returncode
    except subprocess.TimeoutExpired:
        try:
            process.kill()
        except:
            pass
        return -1
    except Exception:
        return -1


def run_pyinstaller(
    py_file: str,
    output_folder: str,
    options: dict
) -> Tuple[int, str]:
    """执行PyInstaller打包"""
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

    build_path = tempfile.gettempdir()

    if output_folder:
        dist_path = output_folder
    else:
        dist_path = str(Path(py_file).parent / "dist")

    cmd.extend(["--distpath", dist_path])
    cmd.extend(["--workpath", build_path])
    cmd.extend(["--specpath", str(Path(py_file).parent)])

    if options.get("icon"):
        cmd.extend(["--icon", options["icon"]])

    if options.get("resource_folder"):
        cmd.extend(["--add-data", f"{options['resource_folder']};."])

    cmd.append(py_file)

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    output_lines = []
    for line in process.stdout:
        output_lines.append(line.strip())

    process.wait()
    return process.returncode, "\n".join(output_lines)
