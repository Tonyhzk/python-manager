# ==================== 依赖管理器 ====================
"""依赖安装业务逻辑管理器"""

import os
import sys
from typing import Callable, Dict, List, Set, Optional

from l5_atom import (
    analyze_py_file,
    analyze_requirements_file,
    analyze_toml_file,
    get_installed_packages,
    install_packages_batch,
    check_module_installed,
)


class DepsManager:
    """依赖管理器"""

    def analyze_file(
        self,
        filepath: str,
        input_type: str,
        stdlib_modules: Set[str]
    ) -> Set[str]:
        """分析文件提取依赖"""
        if input_type == "auto":
            return analyze_py_file(filepath, stdlib_modules)
        elif input_type == "req":
            return analyze_requirements_file(filepath)
        elif input_type == "toml":
            return analyze_toml_file(filepath)
        return set()

    def find_missing_deps(
        self,
        dependencies: Set[str],
        installed: Set[str]
    ) -> Set[str]:
        """找出未安装的依赖"""
        return dependencies - installed

    def check_missing_from_installed(
        self,
        dependencies: Set[str],
        python_path: str = sys.executable
    ) -> Set[str]:
        """检查哪些依赖未安装"""
        missing = set()
        for dep in dependencies:
            if not check_module_installed(dep, python_path):
                missing.add(dep)
        return missing

    def install_missing(
        self,
        missing: Set[str],
        python_path: str = sys.executable,
        log_callback: Callable[[str, str], None] = None
    ) -> Dict[str, dict]:
        """安装缺失的依赖"""
        if not missing:
            return {}

        def default_log(msg, level):
            pass

        if log_callback is None:
            log_callback = default_log

        log_callback(f"开始安装 {len(missing)} 个缺失的库...", "info")
        results = install_packages_batch(sorted(missing), python_path)

        success_count = sum(1 for r in results.values() if r["success"])
        fail_count = len(results) - success_count

        log_callback(f"安装完成: {success_count} 成功, {fail_count} 失败", "info" if fail_count == 0 else "warning")

        return results

    def analyze_and_install(
        self,
        filepath: str,
        input_type: str,
        stdlib_modules: Set[str],
        python_path: str = sys.executable,
        log_callback: Callable[[str, str], None] = None
    ) -> Set[str]:
        """分析并安装依赖的主流程"""
        def default_log(msg, level):
            pass

        if log_callback is None:
            log_callback = default_log

        # 分析依赖
        log_callback(f"分析文件: {filepath}", "info")
        dependencies = self.analyze_file(filepath, input_type, stdlib_modules)

        if not dependencies:
            log_callback("未发现外部依赖", "success")
            return set()

        # 检查已安装的
        log_callback(f"发现 {len(dependencies)} 个依赖", "info")
        installed = get_installed_packages(python_path)

        # 找出缺失的
        missing = self.find_missing_deps(dependencies, installed)

        if missing:
            log_callback(f"缺失 {len(missing)} 个库", "warning")
            self.install_missing(missing, python_path, log_callback)
        else:
            log_callback("所有依赖都已安装", "success")

        return missing

    def get_analysis_result(
        self,
        filepath: str,
        input_type: str,
        stdlib_modules: Set[str]
    ) -> tuple:
        """获取分析结果，返回(依赖集合, 缺失集合)"""
        dependencies = self.analyze_file(filepath, input_type, stdlib_modules)
        installed = get_installed_packages()
        missing = self.find_missing_deps(dependencies, installed)
        return dependencies, missing
