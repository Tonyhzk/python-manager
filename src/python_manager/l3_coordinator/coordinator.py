# ==================== 协调器 ====================
"""工作流协调层 - 连接GUI和业务逻辑"""

from typing import Callable, Dict, List, Set, Tuple, Optional
import threading

from l4_molecule import PackManager, CloneManager, DepsManager, PortablePackager, get_stdlib_modules
from l5_atom import (
    detect_python_versions,
    scan_python_files,
    get_python_info,
    check_module_installed,
    analyze_project_directory,
)


class Coordinator:
    """协调器 - 管理L2与L4的通信"""

    def __init__(self, log_callback: Callable[[str, str], None]):
        self.log_callback = log_callback
        self.stdlib_modules = get_stdlib_modules()

        # 初始化业务逻辑管理器（L4分子）
        self.pack_manager = PackManager()
        self.pack_manager.set_stdlib_modules(self.stdlib_modules)

        self.clone_manager = CloneManager()
        self.deps_manager = DepsManager()
        self.portable_packager = PortablePackager()

    # ======================== PyInstaller相关工作流 ========================

    def get_pyinstaller_version(self) -> Tuple[bool, str]:
        """检查PyInstaller版本"""
        return self.pack_manager.check_pyinstaller()

    def install_pyinstaller(self, python_path: str = None) -> bool:
        """安装PyInstaller"""
        import sys
        if python_path is None:
            python_path = sys.executable
        return self.pack_manager.install_pyinstaller(python_path)

    def detect_icon_files(self, py_file: str, resource_folder: str = "") -> List[str]:
        """检测图标文件"""
        return self.pack_manager.detect_icons(py_file, resource_folder)

    def execute_pack(
        self,
        py_file: str,
        output_folder: str,
        options: Dict,
        on_complete: Callable[[bool, str], None]
    ):
        """执行打包任务（异步）"""
        def run():
            self.log_callback("开始打包...", "info")
            success, dist_path = self.pack_manager.run_pack(
                py_file, output_folder, options, self.log_callback
            )
            on_complete(success, dist_path)

        threading.Thread(target=run, daemon=True).start()

    # ======================== 环境克隆相关工作流 ========================

    def get_python_versions(self) -> List[Dict]:
        """检测系统中的Python版本"""
        return detect_python_versions()

    def execute_clone(
        self,
        mode: int,
        project_dir: str,
        output_dir: str,
        python_path: str,
        include_project: bool,
        compress_zip: bool,
        on_complete: Callable[[bool, str], None]
    ):
        """执行克隆任务（异步）"""
        def run():
            success, target_dir = self.clone_manager.execute_clone(
                mode, project_dir, output_dir, python_path,
                include_project, compress_zip, self.stdlib_modules,
                self.log_callback
            )
            on_complete(success, target_dir)

        threading.Thread(target=run, daemon=True).start()

    # ======================== 依赖分析相关工作流 ========================

    def execute_deps_analysis(
        self,
        filepath: str,
        input_type: str,
        python_path: str,
        on_complete: Callable[[set], None]
    ):
        """执行依赖分析任务（异步）"""
        def run():
            dependencies, missing = self.deps_manager.get_analysis_result(
                filepath, input_type, self.stdlib_modules
            )
            on_complete(missing)

        threading.Thread(target=run, daemon=True).start()

    def execute_deps_install(
        self,
        missing: set,
        python_path: str,
        on_complete: Callable[[int, int], None]
    ):
        """执行依赖安装任务（异步）"""
        def run():
            results = self.deps_manager.install_missing(
                missing, python_path, self.log_callback
            )
            success = sum(1 for r in results.values() if r["success"])
            fail = len(results) - success
            on_complete(success, fail)

        threading.Thread(target=run, daemon=True).start()

    # ======================== 便携式Python打包相关工作流 ========================

    def execute_portable_package(
        self,
        requirements_file: str,
        output_dir: str,
        mode: int = 1,
        include_project: bool = False,
        project_dir: str = None,
        app_name: str = "Application",
        on_complete: Callable[[bool, str], None] = None
    ):
        """执行便携式Python打包任务（异步）"""
        from pathlib import Path

        def run():
            self.log_callback("开始便携式Python打包...", "info")
            success, result = self.portable_packager.execute_package(
                requirements_file=Path(requirements_file),
                output_dir=Path(output_dir),
                mode=mode,
                include_project=include_project,
                project_dir=Path(project_dir) if project_dir else None,
                app_name=app_name,
                log_callback=self.log_callback
            )
            if on_complete:
                on_complete(success, result)

        threading.Thread(target=run, daemon=True).start()

    # ======================== 基础查询工作流 ========================

    def scan_directory(self, directory: str) -> List[str]:
        """扫描目录中的Python文件"""
        from pathlib import Path
        try:
            return [str(f) for f in scan_python_files(Path(directory))]
        except:
            return []

    def check_module(self, module_name: str, python_path: str = None) -> bool:
        """检查模块是否已安装"""
        import sys
        if python_path is None:
            python_path = sys.executable
        return check_module_installed(module_name, python_path)

    def get_project_dependencies(self, project_dir: str) -> Set[str]:
        """分析项目依赖"""
        return analyze_project_directory(project_dir, self.stdlib_modules)

    # ======================== 工具方法 ========================

    def log(self, message: str, level: str = "info"):
        """日志回调"""
        self.log_callback(message, level)
