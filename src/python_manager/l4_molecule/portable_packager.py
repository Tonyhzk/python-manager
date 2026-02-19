# ==================== 便携式Python打包管理器 ====================
"""便携式Python环境打包 - 分子层业务逻辑"""

import sys
from pathlib import Path
from typing import Callable, Tuple, List

from l5_atom import (
    clean_directory,
    create_venv_portable,
    get_pip_path,
    get_installed_packages_portable,
    parse_requirements,
    get_package_dependencies,
    copy_site_packages_from_env,
    install_requirements_in_venv,
    copy_project_files_portable,
    create_launcher_scripts,
    create_readme,
    create_zip_archive,
    generate_output_filename,
)


class PortablePackager:
    """便携式Python环境打包管理器"""

    def __init__(self):
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    def execute_package(
        self,
        requirements_file: Path,
        output_dir: Path,
        mode: int = 1,
        include_project: bool = False,
        project_dir: Path = None,
        app_name: str = "Application",
        log_callback: Callable = None
    ) -> Tuple[bool, str]:
        """执行完整的打包流程

        Args:
            requirements_file: requirements.txt 文件路径
            output_dir: 输出目录
            mode: 1=纯在线, 2=离线克隆模式
            include_project: 是否包含项目文件
            project_dir: 项目目录（如果include_project为True）
            app_name: 应用名称
            log_callback: 日志回调函数

        Returns:
            (成功标志, 输出文件路径或错误信息)
        """
        try:
            build_dir = output_dir / "build_portable"

            # 1. 清理构建目录
            if log_callback:
                log_callback("=" * 80, "info")
                log_callback("步骤 1: 清理构建目录", "info")
                log_callback("=" * 80, "info")
            clean_directory(build_dir)

            # 2. 创建虚拟环境
            if log_callback:
                log_callback("=" * 80, "info")
                log_callback("步骤 2: 创建虚拟环境", "info")
                log_callback("=" * 80, "info")
            venv_path = build_dir / "python_env"
            if not create_venv_portable(venv_path, log_callback):
                return False, "创建虚拟环境失败"

            # 3. 处理依赖
            if log_callback:
                log_callback("=" * 80, "info")
                log_callback("步骤 3: 处理依赖", "info")
                log_callback("=" * 80, "info")

            if mode == 2:  # 离线克隆模式
                success = self._clone_dependencies(venv_path, requirements_file, log_callback)
            else:  # 在线模式
                success = self._download_dependencies(venv_path, requirements_file, log_callback)

            if not success:
                if log_callback:
                    log_callback("⚠ 部分依赖处理失败，但继续打包", "warning")

            # 4. 复制项目文件（如果需要）
            if include_project and project_dir:
                if log_callback:
                    log_callback("=" * 80, "info")
                    log_callback("步骤 4: 复制项目文件", "info")
                    log_callback("=" * 80, "info")
                project_dest = build_dir / app_name
                project_dest.mkdir(exist_ok=True)
                copy_project_files_portable(Path(project_dir), project_dest, log_callback)

            # 5. 创建启动脚本
            if log_callback:
                log_callback("=" * 80, "info")
                log_callback("步骤 5: 创建启动脚本", "info")
                log_callback("=" * 80, "info")
            create_launcher_scripts(build_dir, app_name, log_callback)
            create_readme(build_dir, self.python_version, app_name)

            # 6. 创建ZIP压缩包
            if log_callback:
                log_callback("=" * 80, "info")
                log_callback("步骤 6: 创建 ZIP 压缩包", "info")
                log_callback("=" * 80, "info")

            output_filename = generate_output_filename(self.python_version, app_name)
            dist_dir = output_dir / "dist"
            output_path = create_zip_archive(build_dir, dist_dir, output_filename, log_callback)

            if log_callback:
                log_callback("=" * 80, "info")
                log_callback("✓ 打包完成！", "info")
                log_callback("=" * 80, "info")
                log_callback(f"✓ 输出文件: {output_path}", "info")

            return True, str(output_path)

        except Exception as e:
            if log_callback:
                log_callback(f"✗ 打包过程中出现异常: {e}", "error")
            import traceback
            traceback.print_exc()
            return False, str(e)

    def _clone_dependencies(
        self,
        venv_path: Path,
        requirements_file: Path,
        log_callback: Callable = None
    ) -> bool:
        """从当前环境克隆依赖（离线模式）"""
        if log_callback:
            log_callback("从当前环境克隆依赖（离线模式）", "info")

        pip_path = get_pip_path(venv_path)

        # 获取当前环境的包
        installed_packages = get_installed_packages_portable()
        if log_callback:
            log_callback(f"当前环境共有 {len(installed_packages)} 个已安装的包", "info")

        # 解析requirements
        required_packages = parse_requirements(requirements_file)
        if not required_packages:
            if log_callback:
                log_callback("没有需要安装的依赖", "warning")
            return True

        if log_callback:
            log_callback("-" * 80, "info")
            log_callback("开始从当前环境复制包...", "info")
            log_callback("-" * 80, "info")

        # 收集所有需要复制的包（包括依赖）
        all_packages_to_copy = set()
        failed_packages = []

        for pkg_name, pkg_spec in required_packages:
            pkg_name_lower = pkg_name.lower()

            # 检查包是否在当前环境中
            if pkg_name_lower in installed_packages:
                if log_callback:
                    log_callback(f"✓ 发现: {pkg_name}", "info")
                all_packages_to_copy.add(pkg_name)

                # 获取依赖
                deps = get_package_dependencies(pkg_name)
                if deps and log_callback:
                    log_callback(f"  依赖: {', '.join(deps)}", "info")
                for dep in deps:
                    dep_lower = dep.lower()
                    if dep_lower in installed_packages:
                        all_packages_to_copy.add(dep)
            else:
                if log_callback:
                    log_callback(f"✗ 未安装: {pkg_name}，将稍后从网络下载", "warning")
                failed_packages.append(pkg_spec)

        if log_callback:
            log_callback("-" * 80, "info")
            log_callback(f"需要复制 {len(all_packages_to_copy)} 个包（包含依赖）", "info")

        # 直接复制site-packages
        if all_packages_to_copy:
            if log_callback:
                log_callback("=" * 80, "info")
                log_callback("步骤 3.1: 复制包到虚拟环境", "info")
                log_callback("=" * 80, "info")

            copied = copy_site_packages_from_env(venv_path, all_packages_to_copy, log_callback)
            if log_callback:
                log_callback(f"成功复制 {len(copied)} 个包", "info")

            # 检查哪些包复制失败
            for pkg_name, pkg_spec in required_packages:
                if pkg_name not in copied and pkg_spec not in failed_packages:
                    failed_packages.append(pkg_spec)

        # 如果有失败的包，从网络下载
        if failed_packages:
            if log_callback:
                log_callback("=" * 80, "info")
                log_callback("步骤 3.2: 下载失败的依赖（从网络）", "info")
                log_callback("=" * 80, "info")
                log_callback(f"需要从网络下载 {len(failed_packages)} 个包...", "info")
                log_callback("⚠ 注意：此步骤需要网络连接", "warning")

            success, success_count, fail_count = install_requirements_in_venv(
                pip_path, failed_packages, log_callback
            )

            if log_callback:
                log_callback(f"下载完成: {success_count} 个成功, {fail_count} 个失败", "info")

            return success
        else:
            if log_callback:
                log_callback("依赖安装完成！", "info")
            return True

    def _download_dependencies(
        self,
        venv_path: Path,
        requirements_file: Path,
        log_callback: Callable = None
    ) -> bool:
        """从网络下载依赖（在线模式）"""
        if log_callback:
            log_callback("从网络下载依赖（在线模式）", "info")

        pip_path = get_pip_path(venv_path)

        # 解析requirements
        required_packages = parse_requirements(requirements_file)
        if not required_packages:
            if log_callback:
                log_callback("没有需要安装的依赖", "warning")
            return True

        package_specs = [spec for _, spec in required_packages]

        if log_callback:
            log_callback(f"准备下载 {len(package_specs)} 个包...", "info")

        success, success_count, fail_count = install_requirements_in_venv(
            pip_path, package_specs, log_callback
        )

        if log_callback:
            log_callback(f"下载完成: {success_count} 个成功, {fail_count} 个失败", "info")

        return success
