# ==================== 依赖分析工具 ====================
"""依赖分析相关原子函数"""

import ast
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Set, Optional


def analyze_py_file(filepath: str, stdlib_modules: Set[str]) -> Set[str]:
    """分析Python文件提取依赖"""
    dependencies = set()

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split('.')[0]
                    if module.lower() not in stdlib_modules:
                        dependencies.add(module)
            elif isinstance(node, ast.ImportFrom) and node.module:
                module = node.module.split('.')[0]
                if module.lower() not in stdlib_modules:
                    dependencies.add(module)
    except Exception:
        pass

    return dependencies


def analyze_requirements_file(filepath: str) -> Set[str]:
    """分析requirements.txt文件"""
    dependencies = set()

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('-e'):
                continue
            pkg = re.split(r'[=<>!~]', line)[0].strip().lower()
            if pkg:
                dependencies.add(pkg)
    except Exception:
        pass

    return dependencies


def analyze_toml_file(filepath: str) -> Set[str]:
    """分析pyproject.toml文件"""
    dependencies = set()

    try:
        import toml
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        data = toml.loads(content)
    except Exception:
        try:
            import tomllib
            with open(filepath, 'rb') as f:
                data = tomllib.load(f)
        except Exception:
            return dependencies

    # poetry 项目
    if 'tool' in data and 'poetry' in data['tool']:
        deps = data['tool']['poetry'].get('dependencies', {})
        for pkg in deps.keys():
            if pkg != 'python':
                dependencies.add(pkg.lower())

    # pdm 项目
    if 'tool' in data and 'pdm' in data['tool']:
        deps = data['tool']['pdm'].get('dependencies', {})
        for pkg in deps.keys():
            dependencies.add(pkg.lower())

    # 标准 project.dependencies (PEP 621)
    if 'project' in data:
        deps = data['project'].get('dependencies', [])
        for dep in deps:
            pkg = re.split(r'[=<>!~\[\]]', dep)[0].strip().lower()
            if pkg:
                dependencies.add(pkg)

    return dependencies


def analyze_project_directory(project_dir: str, stdlib_modules: Set[str]) -> List[str]:
    """分析整个项目目录的依赖"""
    all_deps = set()
    project_path = Path(project_dir)

    for py_file in project_path.rglob("*.py"):
        deps = analyze_py_file(str(py_file), stdlib_modules)
        all_deps.update(deps)

    return sorted(all_deps)


def get_installed_packages(python_path: str = sys.executable) -> Set[str]:
    """获取已安装的包列表"""
    packages = set()
    try:
        result = subprocess.run(
            [python_path, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line and not line.startswith('#'):
                    pkg = line.split('==')[0].split('>=')[0].split('<=')[0].split('[')[0].strip().lower()
                    packages.add(pkg)
    except Exception:
        pass
    return packages


def install_package(package_name: str, python_path: str = sys.executable) -> tuple:
    """安装单个包，返回(成功, 输出)"""
    try:
        result = subprocess.run(
            [python_path, "-m", "pip", "install", package_name],
            capture_output=True,
            text=True,
            timeout=120
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


def install_packages_batch(
    packages: List[str],
    python_path: str = sys.executable
) -> dict:
    """批量安装包，返回每个包的结果"""
    results = {}
    for pkg in packages:
        success, output = install_package(pkg, python_path)
        results[pkg] = {"success": success, "output": output}
    return results


def freeze_requirements(python_path: str = sys.executable, output_file: Optional[str] = None) -> str:
    """生成requirements.txt内容"""
    try:
        result = subprocess.run(
            [python_path, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            timeout=30
        )
        content = result.stdout
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
        return content
    except Exception:
        return ""


def download_requirements(
    requirements_file: str,
    target_dir: str,
    python_path: str = sys.executable
) -> bool:
    """下载依赖包到指定目录"""
    try:
        result = subprocess.run(
            [
                python_path, "-m", "pip", "download",
                "-r", requirements_file,
                "-d", target_dir
            ],
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode == 0
    except Exception:
        return False
