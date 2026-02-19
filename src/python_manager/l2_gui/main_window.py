# ==================== 主窗口 ====================
"""主窗口GUI组件 - 完整版"""

import json
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from pathlib import Path
from urllib.parse import unquote

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText

from l0_resource import (
    APP_NAME,
    APP_VERSION,
    DEFAULT_THEME,
    THEME_LIGHT,
    THEME_DARK,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_MIN_HEIGHT,
    get_config_path,
    get_base_path,
)
from l3_coordinator import Coordinator
from l5_atom import (
    get_stdlib_modules,
    locate_file,
    open_folder,
)

# ==================== 拖拽检测（条件导入）====================
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_SUPPORT = True
except ImportError:
    DND_SUPPORT = False


# ==================== 动态选择窗口基类 ====================
if DND_SUPPORT:
    BaseWindow = TkinterDnD.Tk
else:
    BaseWindow = tk.Tk


class MainWindow(BaseWindow):
    """主窗口"""

    def __init__(self):
        # 1. 先调用父类初始化
        super().__init__()

        # 2. 窗口基本设置
        self.title(f"{APP_NAME} {APP_VERSION}")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.attributes('-topmost', True)  # 默认置顶

        # 3. 应用 ttkbootstrap 主题
        self.style = ttk.Style()
        self.style.theme_use(DEFAULT_THEME)

        # 4. 初始化L3协调器
        self.commander = Coordinator(log_callback=self.log)

        # 5. 配置数据
        self.config_data = {
            "theme": DEFAULT_THEME,
            # 标签页1: 打包配置
            "py_file_path": "",
            "resource_folder": "",
            "output_folder": "",
            "icon_path": "",
            "onefile": True,
            "windowed": True,
            "console": False,
            # 标签页2: 环境克隆配置
            "clone_mode": 2,
            "clone_project_path": "",
            "clone_output_path": "",
            "clone_interpreter": sys.executable,
            "clone_include_project": True,
            "clone_compress_zip": True,
            # 标签页3: 依赖安装配置
            "last_import_file": "",
            # 标签页4: 便携式Python打包配置
            "portable_requirements_file": "",
            "portable_output_dir": "",
            "portable_mode": 2,
            "portable_include_project": False,
            "portable_project_dir": "",
            "portable_app_name": "MyApplication",
        }

        # 6. 状态变量
        self.is_processing = False
        self.stdlib_modules = self.commander.stdlib_modules
        self.missing_libs = set()

        # 7. 加载配置
        self.load_config()

        # 8. 构建UI
        self.setup_ui()

        # 9. 居中窗口
        self.center_window()

        # 10. 拖拽功能
        if DND_SUPPORT:
            self.setup_drag_and_drop()

        # 11. 绑定快捷键
        self.bind_shortcuts()

    def load_config(self):
        """加载配置"""
        config_path = get_config_path()
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    self.config_data.update(saved)
            except Exception as e:
                pass

    def save_config(self):
        """保存配置"""
        try:
            config_path = get_config_path()
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.log(f"保存配置失败: {e}", "error")

    def center_window(self):
        """窗口居中"""
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

    # ==================== 界面布局 ====================
    def setup_ui(self):
        """构建主界面"""
        # 主容器
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # 顶部标题栏
        self.create_title_bar(main_frame)

        # 创建Notebook（标签页）
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=BOTH, expand=True, pady=10)

        # 创建四个标签页
        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)
        self.tab3 = ttk.Frame(self.notebook)
        self.tab4 = ttk.Frame(self.notebook)

        self.notebook.add(self.tab1, text="  📦 PyInstaller打包 ")
        self.notebook.add(self.tab2, text="  🐍 环境克隆 ")
        self.notebook.add(self.tab3, text="  📚 依赖安装 ")
        self.notebook.add(self.tab4, text="  🌐 便携式Python ")

        # 构建每个标签页的内容
        self.setup_tab1_pyinstaller()
        self.setup_tab2_clone()
        self.setup_tab3_dependency()
        self.setup_tab4_portable()

        # 底部：日志区域（统一）
        self.create_log_panel(main_frame)

        # 底部：状态栏
        self.create_status_bar(main_frame)

        # 绑定标签切换事件
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def create_title_bar(self, parent):
        """创建标题栏"""
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill=X, pady=(0, 10))

        # 标题
        title_label = ttk.Label(
            title_frame,
            text="Python 管理工具箱",
            font=("Microsoft YaHei UI", 16, "bold")
        )
        title_label.pack(side=LEFT)

        # 主题切换按钮
        self.theme_btn = ttk.Button(
            title_frame,
            text="🌙 暗黑模式",
            command=self.toggle_theme,
            width=15
        )
        self.theme_btn.pack(side=RIGHT)

        # 窗口置顶切换按钮
        self.topmost_var = tk.BooleanVar(value=self.attributes('-topmost'))
        self.topmost_btn = ttk.Button(
            title_frame,
            text="📌 取消置顶" if self.attributes('-topmost') else "📌 置顶",
            command=self.toggle_topmost,
            width=10
        )
        self.topmost_btn.pack(side=RIGHT, padx=(0, 10))

    def toggle_theme(self):
        """切换主题"""
        current = self.config_data.get("theme", DEFAULT_THEME)
        if current == THEME_DARK:
            new_theme = THEME_LIGHT
            self.theme_btn.config(text="☀️ 明亮模式")
        else:
            new_theme = THEME_DARK
            self.theme_btn.config(text="🌙 暗黑模式")

        self.config_data["theme"] = new_theme
        self.style.theme_use(new_theme)
        self.save_config()
        self.update_log_colors()

    def toggle_topmost(self):
        """切换窗口置顶"""
        self.attributes('-topmost', not self.attributes('-topmost'))
        self.topmost_var.set(self.attributes('-topmost'))
        if self.attributes('-topmost'):
            self.topmost_btn.config(text="📌 取消置顶")
        else:
            self.topmost_btn.config(text="📌 置顶")

    def on_tab_changed(self, event):
        """标签页切换事件"""
        self.save_config()

    # ==================== 标签页1: PyInstaller打包 ====================
    def setup_tab1_pyinstaller(self):
        """构建PyInstaller打包标签页"""
        # 上下分栏
        self.paned_tab1 = ttk.PanedWindow(self.tab1, orient=VERTICAL)
        self.paned_tab1.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # 上方：选项区
        top_panel = ttk.Frame(self.paned_tab1)
        self.paned_tab1.add(top_panel, weight=2)

        # 文件选择
        file_frame = ttk.LabelFrame(top_panel, text=" 文件选择 ", padding=10)
        file_frame.pack(fill=X, pady=(0, 10))

        self.tab1_path_entry = ttk.Entry(file_frame, font=("Microsoft YaHei UI", 10))
        self.tab1_path_entry.pack(fill=X, pady=(0, 5))
        self.tab1_path_entry.insert(0, self.config_data.get("py_file_path", ""))

        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=X)

        ttk.Button(btn_frame, text="浏览文件...", command=self.tab1_browse_file, width=15).pack(side=LEFT)
        ttk.Button(btn_frame, text="📂 定位", command=self.tab1_locate_file, width=10).pack(side=LEFT, padx=(10, 0))
        ttk.Button(btn_frame, text="扫描当前目录", command=self.tab1_scan_directory, width=15).pack(side=LEFT, padx=(10, 0))

        # 打包选项
        options_frame = ttk.LabelFrame(top_panel, text=" 打包选项 ", padding=10)
        options_frame.pack(fill=X, pady=(0, 10))

        self.tab1_onefile_var = tk.BooleanVar(value=self.config_data.get("onefile", True))
        ttk.Checkbutton(options_frame, text="单文件打包 (--onefile)", variable=self.tab1_onefile_var).pack(anchor=W)

        self.tab1_windowed_var = tk.BooleanVar(value=self.config_data.get("windowed", True))
        ttk.Checkbutton(options_frame, text="窗口应用 (--windowed，无控制台)", variable=self.tab1_windowed_var).pack(anchor=W)

        self.tab1_console_var = tk.BooleanVar(value=self.config_data.get("console", False))
        ttk.Checkbutton(options_frame, text="显示控制台 (调试用)", variable=self.tab1_console_var).pack(anchor=W)

        # 资源文件夹
        resource_frame = ttk.LabelFrame(top_panel, text=" 资源文件夹 ", padding=10)
        resource_frame.pack(fill=X)

        self.tab1_resource_entry = ttk.Entry(resource_frame, font=("Microsoft YaHei UI", 10))
        self.tab1_resource_entry.pack(fill=X, pady=(0, 5))
        self.tab1_resource_entry.insert(0, self.config_data.get("resource_folder", ""))

        btn_frame2 = ttk.Frame(resource_frame)
        btn_frame2.pack(fill=X)

        ttk.Button(btn_frame2, text="选择文件夹...", command=self.tab1_browse_resource, width=15).pack(side=LEFT)
        ttk.Button(btn_frame2, text="📂 打开", command=self.tab1_open_resource, width=10).pack(side=LEFT, padx=(10, 0))
        for folder in ["res", "templates", "static", "assets"]:
            ttk.Button(btn_frame2, text=folder, width=8,
                      command=lambda f=folder: self.tab1_set_resource(f)).pack(side=LEFT, padx=5)

        # 绑定拖放（支持文件夹拖拽）
        if DND_SUPPORT:
            self.tab1_resource_entry.drop_target_register(DND_FILES)
            self.tab1_resource_entry.dnd_bind('<<Drop>>', lambda e: self.tab1_on_resource_drop(e))

        # ==================== 图标设置 ====================
        icon_frame = ttk.LabelFrame(top_panel, text=" 程序图标 ", padding=10)
        icon_frame.pack(fill=X, pady=(10, 0))

        self.tab1_icon_entry = ttk.Entry(icon_frame, font=("Microsoft YaHei UI", 10))
        self.tab1_icon_entry.pack(fill=X, pady=(0, 5))
        self.tab1_icon_entry.insert(0, self.config_data.get("icon_path", ""))

        btn_frame_icon = ttk.Frame(icon_frame)
        btn_frame_icon.pack(fill=X)

        ttk.Button(btn_frame_icon, text="浏览文件...", command=self.tab1_browse_icon, width=12).pack(side=LEFT)
        ttk.Button(btn_frame_icon, text="📄 定位", command=self.tab1_locate_icon, width=10).pack(side=LEFT, padx=(10, 0))
        ttk.Button(btn_frame_icon, text="自动检测", command=self.tab1_detect_icons, width=10).pack(side=LEFT, padx=(10, 0))
        ttk.Button(btn_frame_icon, text="刷新", command=self.tab1_detect_icons, width=8).pack(side=LEFT, padx=5)

        # 检测到的图标预览
        self.tab1_icon_preview = ttk.Label(icon_frame, text="未选择图标", foreground="gray")
        self.tab1_icon_preview.pack(anchor=W, pady=(5, 0))

        # 支持的图标格式
        ttk.Label(icon_frame, text="支持 .ico, .icns, .png 格式", foreground="gray", font=("Microsoft YaHei UI", 8)).pack(anchor=W)

        # 绑定拖放（支持图标文件拖拽）
        if DND_SUPPORT:
            self.tab1_icon_entry.drop_target_register(DND_FILES)
            self.tab1_icon_entry.dnd_bind('<<Drop>>', lambda e: self.tab1_on_icon_drop(e))

        # ==================== 输出目录设置 ====================
        output_frame = ttk.LabelFrame(top_panel, text=" 输出目录 ", padding=10)
        output_frame.pack(fill=X, pady=(10, 0))

        self.tab1_output_entry = ttk.Entry(output_frame, font=("Microsoft YaHei UI", 10))
        self.tab1_output_entry.pack(fill=X, pady=(0, 5))
        self.tab1_output_entry.insert(0, self.config_data.get("output_folder", ""))

        btn_frame_output = ttk.Frame(output_frame)
        btn_frame_output.pack(fill=X)

        ttk.Button(btn_frame_output, text="浏览...", command=self.tab1_browse_output, width=12).pack(side=LEFT)
        ttk.Button(btn_frame_output, text="📂 打开", command=self.tab1_open_output, width=10).pack(side=LEFT, padx=(10, 0))
        ttk.Button(btn_frame_output, text="脚本目录", command=self.tab1_set_output_to_script_dir, width=12).pack(side=LEFT, padx=(10, 0))
        ttk.Button(btn_frame_output, text="清空", command=lambda: self.tab1_output_entry.delete(0, END), width=8).pack(side=LEFT, padx=5)

        # 提示文字
        ttk.Label(output_frame, text="留空则输出到被打包脚本所在目录，设置后PyInstaller会在该目录创建dist",
                 foreground="gray", font=("Microsoft YaHei UI", 8)).pack(anchor=W)

        # 绑定拖放（支持文件夹拖拽）
        if DND_SUPPORT:
            self.tab1_output_entry.drop_target_register(DND_FILES)
            self.tab1_output_entry.dnd_bind('<<Drop>>', lambda e: self.tab1_on_output_drop(e))

        # 下方：操作按钮
        bottom_panel = ttk.Frame(self.paned_tab1)
        self.paned_tab1.add(bottom_panel, weight=1)

        # PyInstaller版本和状态
        info_frame = ttk.Frame(bottom_panel)
        info_frame.pack(fill=X, pady=(0, 10))

        self.tab1_pyinstaller_version = ttk.Label(info_frame, text="PyInstaller: 检测中...", foreground="gray")
        self.tab1_pyinstaller_version.pack(side=LEFT)

        ttk.Button(info_frame, text="刷新状态", command=self.tab1_check_pyinstaller, width=10).pack(side=LEFT, padx=10)

        # 操作按钮
        btn_panel = ttk.Frame(bottom_panel)
        btn_panel.pack()

        self.tab1_install_btn = ttk.Button(btn_panel, text="安装PyInstaller", command=self.tab1_install_pyinstaller, width=15)
        self.tab1_install_btn.pack(side=LEFT, padx=5)

        self.tab1_pack_btn = ttk.Button(btn_panel, text="开始打包", command=self.tab1_start_pack, width=15)
        self.tab1_pack_btn.pack(side=LEFT, padx=5)

        # 初始检查
        self.tab1_check_pyinstaller()

    def tab1_set_resource(self, folder):
        """设置资源文件夹"""
        self.tab1_resource_entry.delete(0, END)
        self.tab1_resource_entry.insert(0, folder)

    def tab1_locate_file(self):
        """定位Python文件"""
        locate_file(self.tab1_path_entry.get().strip())

    def tab1_open_resource(self):
        """打开资源文件夹"""
        open_folder(self.tab1_resource_entry.get().strip())

    def tab1_locate_icon(self):
        """定位图标文件"""
        locate_file(self.tab1_icon_entry.get().strip())

    def tab1_open_output(self):
        """打开输出目录"""
        open_folder(self.tab1_output_entry.get().strip())

    def tab1_browse_file(self):
        """浏览选择Python文件"""
        filepath = filedialog.askopenfilename(title="选择Python文件", filetypes=[("Python文件", "*.py"), ("所有文件", "*.*")])
        if filepath:
            self.tab1_path_entry.delete(0, END)
            self.tab1_path_entry.insert(0, filepath)

    def tab1_scan_directory(self):
        """扫描当前目录的Python文件"""
        base_path = get_base_path()
        py_files = list(base_path.glob("*.py"))

        if not py_files:
            messagebox.showinfo("扫描结果", "当前目录未找到.py文件")
            return

        file_list = "\n".join([f"{i+1}. {f.name}" for i, f in enumerate(py_files)])

        if len(py_files) == 1:
            selected = py_files[0]
        else:
            selection = simpledialog.askinteger("选择文件", f"找到{len(py_files)}个Python文件:\n\n{file_list}\n\n请输入序号:", parent=self)
            if selection and 1 <= selection <= len(py_files):
                selected = py_files[selection - 1]
            else:
                return

        self.tab1_path_entry.delete(0, END)
        self.tab1_path_entry.insert(0, str(selected))

    def tab1_browse_resource(self):
        """浏览选择资源文件夹"""
        folder = filedialog.askdirectory(title="选择资源文件夹")
        if folder:
            self.tab1_resource_entry.delete(0, END)
            self.tab1_resource_entry.insert(0, folder)

    def tab1_browse_icon(self):
        """浏览选择图标文件"""
        filepath = filedialog.askopenfilename(
            title="选择程序图标",
            filetypes=[
                ("图标文件", "*.ico"),
                ("PNG图片", "*.png"),
                ("ICNS图标", "*.icns"),
                ("所有文件", "*.*")
            ]
        )
        if filepath:
            self.tab1_icon_entry.delete(0, END)
            self.tab1_icon_entry.insert(0, filepath)
            self.tab1_update_icon_preview(filepath)

    def tab1_on_icon_drop(self, event):
        """处理图标拖放"""
        data = event.data
        if data.startswith("{") and data.endswith("}"):
            data = data[1:-1]
        elif data.startswith("file://"):
            data = unquote(data.replace("file://", ""))

        # 支持图标格式
        if data.endswith((".ico", ".png", ".icns")):
            self.tab1_icon_entry.delete(0, END)
            self.tab1_icon_entry.insert(0, data)
            self.tab1_update_icon_preview(data)
            self.log(f"拖入图标: {data}", "info")
        else:
            self.log("只支持 .ico, .png, .icns 图标文件", "warning")

    def tab1_on_resource_drop(self, event):
        """处理资源文件夹拖放"""
        data = event.data
        if data.startswith("{") and data.endswith("}"):
            data = data[1:-1]
        elif data.startswith("file://"):
            data = unquote(data.replace("file://", ""))

        # 检查是否为目录
        if os.path.isdir(data):
            self.tab1_resource_entry.delete(0, END)
            self.tab1_resource_entry.insert(0, data)
            self.log(f"拖入资源文件夹: {data}", "info")
        elif data.endswith("/") or data.endswith("\\"):
            path = data.rstrip("/\\")
            if os.path.isdir(path):
                self.tab1_resource_entry.delete(0, END)
                self.tab1_resource_entry.insert(0, path)
                self.log(f"拖入资源文件夹: {path}", "info")
            else:
                self.log("路径不存在或不是文件夹", "warning")
        else:
            self.log("只支持文件夹拖放", "warning")

    def tab1_browse_output(self):
        """浏览选择输出目录"""
        folder = filedialog.askdirectory(title="选择输出目录")
        if folder:
            self.tab1_output_entry.delete(0, END)
            self.tab1_output_entry.insert(0, folder)

    def tab1_set_output_to_script_dir(self):
        """将输出目录设置为脚本所在目录"""
        py_file = self.tab1_path_entry.get().strip()
        if py_file:
            script_dir = str(Path(py_file).parent.absolute())
            self.tab1_output_entry.delete(0, END)
            self.tab1_output_entry.insert(0, script_dir)
            self.log(f"输出目录已设置为脚本目录: {script_dir}", "info")
        else:
            messagebox.showwarning("提示", "请先选择Python文件")

    def tab1_on_output_drop(self, event):
        """处理输出目录拖放"""
        data = event.data
        if data.startswith("{") and data.endswith("}"):
            data = data[1:-1]
        elif data.startswith("file://"):
            data = unquote(data.replace("file://", ""))

        if os.path.isdir(data):
            self.tab1_output_entry.delete(0, END)
            self.tab1_output_entry.insert(0, data)
            self.log(f"拖入输出目录: {data}", "info")
        elif data.endswith("/") or data.endswith("\\"):
            path = data.rstrip("/\\")
            if os.path.isdir(path):
                self.tab1_output_entry.delete(0, END)
                self.tab1_output_entry.insert(0, path)
                self.log(f"拖入输出目录: {path}", "info")
            else:
                self.log("路径不存在或不是文件夹", "warning")
        else:
            self.log("只支持文件夹拖放", "warning")

    def tab1_detect_icons(self):
        """自动检测图标文件"""
        py_file = self.tab1_path_entry.get().strip()
        if not py_file:
            messagebox.showwarning("提示", "请先选择Python文件")
            return

        py_path = Path(py_file)
        base_dir = py_path.parent
        search_dirs = [base_dir]

        # 查找资源文件夹
        resource_folder = self.tab1_resource_entry.get().strip()
        if resource_folder:
            res_path = Path(resource_folder)
            if res_path.exists() and res_path.is_dir():
                search_dirs.append(res_path)

        # 检测图标文件
        icon_patterns = ["icon", "app_icon", "logo", "favicon"]
        icon_extensions = [".ico", ".icns", ".png"]

        detected_icons = []

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            for pattern in icon_patterns:
                for ext in icon_extensions:
                    icon_path = search_dir / f"{pattern}{ext}"
                    if icon_path.exists():
                        detected_icons.append(str(icon_path))
                        break

        if detected_icons:
            self.tab1_icon_entry.delete(0, END)
            self.tab1_icon_entry.insert(0, detected_icons[0])
            self.tab1_update_icon_preview(detected_icons[0])
            self.log(f"检测到图标: {detected_icons[0]}", "info")
        else:
            self.tab1_icon_preview.config(text="未检测到图标文件", foreground="orange")
            self.log("未检测到图标文件，请手动选择", "warning")

    def tab1_update_icon_preview(self, icon_path):
        """更新图标预览"""
        if icon_path and Path(icon_path).exists():
            icon_name = Path(icon_path).name
            self.tab1_icon_preview.config(text=f"已选择: {icon_name}", foreground="green")
            self.config_data["icon_path"] = icon_path
        else:
            self.tab1_icon_preview.config(text="未选择图标", foreground="gray")

    def tab1_check_pyinstaller(self):
        """检查PyInstaller版本"""
        installed, version = self.commander.get_pyinstaller_version()
        if installed:
            self.tab1_pyinstaller_version.config(text=f"PyInstaller: {version}")
            return True
        else:
            self.tab1_pyinstaller_version.config(text="PyInstaller: 未安装")
            return False

    def tab1_install_pyinstaller(self):
        """安装PyInstaller"""
        self.log("正在安装PyInstaller...", "info")
        self.tab1_install_btn.config(state=DISABLED)

        def on_install_result(success):
            self.after(0, lambda: self.tab1_install_btn.config(state=NORMAL))
            if success:
                self.after(0, lambda: self.log("PyInstaller安装成功!", "info"))
                self.after(0, lambda: self.tab1_check_pyinstaller())
            else:
                self.after(0, lambda: self.log("安装失败，请检查日志", "error"))

        def install_task():
            success = self.commander.install_pyinstaller(sys.executable)
            on_install_result(success)

        threading.Thread(target=install_task, daemon=True).start()

    def tab1_start_pack(self):
        """开始打包"""
        # 保存配置
        self.config_data["onefile"] = self.tab1_onefile_var.get()
        self.config_data["windowed"] = self.tab1_windowed_var.get()
        self.config_data["console"] = self.tab1_console_var.get()
        self.config_data["py_file_path"] = self.tab1_path_entry.get()
        self.config_data["resource_folder"] = self.tab1_resource_entry.get()
        self.config_data["icon_path"] = self.tab1_icon_entry.get().strip()
        self.save_config()

        py_file = self.tab1_path_entry.get().strip()
        if not py_file:
            messagebox.showerror("错误", "请先选择要打包的Python文件")
            return

        py_path = Path(py_file)
        if not py_path.exists():
            messagebox.showerror("错误", f"文件不存在: {py_file}")
            return

        # 如果输出目录为空，自动填入脚本所在目录
        output_folder = self.tab1_output_entry.get().strip()
        if not output_folder:
            output_folder = str(py_path.parent.absolute())
            self.tab1_output_entry.delete(0, END)
            self.tab1_output_entry.insert(0, output_folder)
            self.config_data["output_folder"] = output_folder
            self.save_config()
            self.log(f"自动设置输出目录: {output_folder}", "info")

        if not self.tab1_check_pyinstaller():
            if not messagebox.askyesno("PyInstaller未安装", "是否立即安装PyInstaller？"):
                return
            self.tab1_install_pyinstaller()
            return

        # 开始打包
        self.is_processing = True
        self.tab1_pack_btn.config(state=DISABLED, text="打包中...")
        self.log("=" * 50, "info")

        # 收集需要的参数
        pack_options = {
            "onefile": self.tab1_onefile_var.get(),
            "windowed": self.tab1_windowed_var.get(),
            "console": self.tab1_console_var.get(),
            "icon_path": self.tab1_icon_entry.get().strip(),
            "resource_folder": self.tab1_resource_entry.get().strip(),
        }

        def on_pack_complete(success: bool, dist_path: str):
            self.after(0, lambda: self.tab1_on_pack_finished(success, dist_path))

        # 通过coordinator执行打包
        self.commander.execute_pack(str(py_path), output_folder, pack_options, on_pack_complete)

    def tab1_on_pack_finished(self, success: bool, dist_path: str):
        """打包完成回调"""
        self.is_processing = False
        self.tab1_pack_btn.config(state=NORMAL, text="开始打包")

        if success:
            self.log("=" * 50, "info")
            self.log(f"打包成功! 输出目录: {dist_path}", "info")
            messagebox.showinfo("成功", f"打包完成!\n\n输出目录: {dist_path}")
            self.status_var.set("打包完成")
        else:
            self.log("打包失败，请检查上方日志", "error")
            self.status_var.set("打包失败")

    # ==================== 标签页2: 环境克隆 ====================
    def setup_tab2_clone(self):
        """构建环境克隆标签页"""
        main_frame = ttk.Frame(self.tab2, padding=10)
        main_frame.pack(fill=BOTH, expand=True)

        # ==================== Python版本选择区域 ====================
        version_frame = ttk.LabelFrame(main_frame, text=" Python版本 ", padding=10)
        version_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(version_frame, text="检测到以下Python版本:").pack(anchor=W)

        self.tab2_python_list = []
        self.tab2_python_combo = ttk.Combobox(version_frame, state="readonly", width=50)
        self.tab2_python_combo.pack(fill=X, pady=5)

        btn_frame_version = ttk.Frame(version_frame)
        btn_frame_version.pack(fill=X)
        ttk.Button(btn_frame_version, text="刷新检测", command=self.tab2_refresh_python_list, width=12).pack(side=LEFT)
        ttk.Button(btn_frame_version, text="自定义路径...", command=self.tab2_custom_interpreter, width=12).pack(side=LEFT, padx=(10, 0))

        self.tab2_interpreter_entry = ttk.Entry(version_frame, font=("Microsoft YaHei UI", 9))
        self.tab2_interpreter_entry.pack(fill=X, pady=(5, 0))
        self.tab2_interpreter_entry.insert(0, self.config_data.get("clone_interpreter", sys.executable))

        btn_frame_interpreter = ttk.Frame(version_frame)
        btn_frame_interpreter.pack(fill=X, pady=(0, 5))
        ttk.Button(btn_frame_interpreter, text="📄 定位", width=10,
                  command=lambda: locate_file(self.tab2_interpreter_entry.get().strip())).pack(side=LEFT)

        # 拖拽支持 - Python解释器
        if DND_SUPPORT:
            self.tab2_interpreter_entry.drop_target_register(DND_FILES)
            self.tab2_interpreter_entry.dnd_bind('<<Drop>>', lambda e: self.tab2_on_interpreter_drop(e))

        # 初始检测
        self.tab2_refresh_python_list()

        # 模式选择
        mode_frame = ttk.LabelFrame(main_frame, text=" 打包模式 ", padding=10)
        mode_frame.pack(fill=X, pady=(0, 10))

        self.tab2_mode_var = tk.IntVar(value=self.config_data.get("clone_mode", 2))
        ttk.Radiobutton(mode_frame, text="【推荐】暴力克隆模式 - 完整复制Python环境，Win到Win免安装",
                       variable=self.tab2_mode_var, value=2, command=self.tab2_on_mode_change).pack(anchor=W)
        ttk.Radiobutton(mode_frame, text="纯净克隆模式 - 仅复制Python核心，体积小需pip安装依赖",
                       variable=self.tab2_mode_var, value=3, command=self.tab2_on_mode_change).pack(anchor=W, pady=(5, 0))
        ttk.Radiobutton(mode_frame, text="标准依赖模式 - 仅下载whl安装包，体积最小",
                       variable=self.tab2_mode_var, value=1, command=self.tab2_on_mode_change).pack(anchor=W, pady=(5, 0))

        # 路径设置
        path_frame = ttk.LabelFrame(main_frame, text=" 路径设置 ", padding=10)
        path_frame.pack(fill=X, pady=(0, 10))

        # 项目源码
        self.tab2_include_project = tk.BooleanVar(value=self.config_data.get("clone_include_project", True))
        ttk.Checkbutton(path_frame, text="包含项目源码", variable=self.tab2_include_project,
                       command=self.tab2_toggle_project_input).pack(anchor=W)

        ttk.Label(path_frame, text="项目源码路径:").pack(anchor=W)
        self.tab2_project_entry = ttk.Entry(path_frame)
        self.tab2_project_entry.pack(fill=X, pady=5)
        self.tab2_project_entry.insert(0, self.config_data.get("clone_project_path", ""))

        btn_frame = ttk.Frame(path_frame)
        btn_frame.pack(fill=X)
        ttk.Button(btn_frame, text="浏览...", command=self.tab2_browse_project, width=10).pack(side=LEFT)
        ttk.Button(btn_frame, text="📂 打开", width=10,
                  command=lambda: open_folder(self.tab2_project_entry.get().strip())).pack(side=LEFT, padx=(10, 0))

        # 拖拽支持 - 项目源码
        if DND_SUPPORT:
            self.tab2_project_entry.drop_target_register(DND_FILES)
            self.tab2_project_entry.dnd_bind('<<Drop>>', lambda e: self.tab2_on_project_drop(e))

        self.tab2_toggle_project_input()

        # 输出路径
        ttk.Label(path_frame, text="打包输出路径:").pack(anchor=W, pady=(10, 0))
        self.tab2_output_entry = ttk.Entry(path_frame)
        self.tab2_output_entry.pack(fill=X, pady=5)
        self.tab2_output_entry.insert(0, self.config_data.get("clone_output_path", ""))

        btn_frame_output = ttk.Frame(path_frame)
        btn_frame_output.pack(fill=X)
        ttk.Button(btn_frame_output, text="浏览...", command=self.tab2_browse_output, width=10).pack(side=LEFT)
        ttk.Button(btn_frame_output, text="📂 打开", width=10,
                  command=lambda: open_folder(self.tab2_output_entry.get().strip())).pack(side=LEFT, padx=(10, 0))

        # 拖拽支持 - 输出路径
        if DND_SUPPORT:
            self.tab2_output_entry.drop_target_register(DND_FILES)
            self.tab2_output_entry.dnd_bind('<<Drop>>', lambda e: self.tab2_on_output_drop(e))

        # 选项
        option_frame = ttk.LabelFrame(main_frame, text=" 附加选项 ", padding=10)
        option_frame.pack(fill=X, pady=(0, 10))

        self.tab2_compress_var = tk.BooleanVar(value=self.config_data.get("clone_compress_zip", True))
        ttk.Checkbutton(option_frame, text="完成后压缩为ZIP包", variable=self.tab2_compress_var).pack(anchor=W)

        # 开始按钮
        self.tab2_start_btn = ttk.Button(main_frame, text="开始执行", command=self.tab2_start_clone, bootstyle="success")
        self.tab2_start_btn.pack(pady=10)
        self.tab2_on_mode_change()

        # 绑定下拉选择事件
        self.tab2_python_combo.bind("<<ComboboxSelected>>", self.tab2_on_python_selected)

    def tab2_refresh_python_list(self):
        """刷新检测Python版本列表"""
        self.tab2_python_list = self.commander.get_python_versions()

        if self.tab2_python_list:
            options = []
            current_path = self.tab2_interpreter_entry.get()
            current_idx = 0

            for i, py_info in enumerate(self.tab2_python_list):
                label = f"Python {py_info['version']} - {py_info['path']}"
                options.append(label)
                if py_info["path"] == current_path:
                    current_idx = i

            self.tab2_python_combo["values"] = options
            self.tab2_python_combo.current(current_idx)
            self.tab2_python_combo.config(state="readonly")
        else:
            self.tab2_python_combo["values"] = ["使用当前Python"]
            self.tab2_python_combo.current(0)
            self.tab2_python_combo.config(state="disabled")

    def tab2_on_python_selected(self, event):
        """Python版本下拉选择事件"""
        idx = self.tab2_python_combo.current()
        if idx >= 0 and idx < len(self.tab2_python_list):
            selected = self.tab2_python_list[idx]
            self.tab2_interpreter_entry.delete(0, END)
            self.tab2_interpreter_entry.insert(0, selected["path"])
            self.log(f"已选择: Python {selected['version']}", "info")

    def tab2_custom_interpreter(self):
        """自定义Python解释器路径"""
        filepath = filedialog.askopenfilename(title="选择Python解释器", filetypes=[("Python解释器", "python*"), ("所有文件", "*.*")])
        if filepath:
            self.tab2_interpreter_entry.delete(0, END)
            self.tab2_interpreter_entry.insert(0, filepath)
            self.log(f"自定义路径: {filepath}", "info")

    def tab2_on_mode_change(self):
        """模式切换"""
        mode = self.tab2_mode_var.get()
        if mode == 2:
            self.tab2_start_btn.config(text="开始克隆 (完整环境)")
        elif mode == 3:
            self.tab2_start_btn.config(text="开始克隆 (纯净核心)")
        else:
            self.tab2_start_btn.config(text="开始下载 (pip download)")

    def tab2_toggle_project_input(self):
        """切换项目输入框状态"""
        if self.tab2_include_project.get():
            self.tab2_project_entry.config(state=NORMAL)
        else:
            self.tab2_project_entry.config(state=DISABLED)

    def tab2_browse_project(self):
        """浏览选择项目目录"""
        path = filedialog.askdirectory()
        if path:
            self.tab2_project_entry.delete(0, END)
            self.tab2_project_entry.insert(0, path)

    def tab2_browse_output(self):
        """浏览选择输出目录"""
        path = filedialog.askdirectory()
        if path:
            self.tab2_output_entry.delete(0, END)
            self.tab2_output_entry.insert(0, path)

    def tab2_start_clone(self):
        """开始环境克隆"""
        # 保存配置
        self.config_data["clone_mode"] = self.tab2_mode_var.get()
        self.config_data["clone_project_path"] = self.tab2_project_entry.get()
        self.config_data["clone_output_path"] = self.tab2_output_entry.get()
        self.config_data["clone_interpreter"] = self.tab2_interpreter_entry.get()
        self.config_data["clone_include_project"] = self.tab2_include_project.get()
        self.config_data["clone_compress_zip"] = self.tab2_compress_var.get()
        self.save_config()

        project = self.tab2_project_entry.get()
        output = self.tab2_output_entry.get()
        python_exe = self.tab2_interpreter_entry.get()
        mode = self.tab2_mode_var.get()
        include_project = self.tab2_include_project.get()

        if include_project and (not project or not os.path.exists(project)):
            messagebox.showerror("错误", "请选择有效的项目源码路径，或取消勾选'包含项目源码'")
            return

        if not output or not os.path.exists(output):
            messagebox.showerror("错误", "输出路径无效")
            return

        self.is_processing = True
        self.tab2_start_btn.config(state=DISABLED, text="处理中...")
        self.log("=" * 50, "info")

        def on_clone_complete(success: bool, target_dir: str):
            self.after(0, lambda: self.tab2_on_clone_finished(success, target_dir))

        # 通过coordinator执行克隆
        self.commander.execute_clone(
            mode, project, output, python_exe, include_project,
            self.tab2_compress_var.get(), on_clone_complete
        )

    def tab2_on_clone_finished(self, success: bool, target_dir: str):
        """克隆完成回调"""
        self.is_processing = False
        self.tab2_start_btn.config(state=NORMAL)
        self.tab2_on_mode_change()

        if success:
            self.log("=" * 50, "info")
            self.log(f"克隆完成! 输出目录: {target_dir}", "info")
            messagebox.showinfo("成功", f"打包完成!\n路径: {target_dir}")
            self.status_var.set("处理完成")
        else:
            self.log("克隆失败，请检查上方日志", "error")
            self.status_var.set("处理失败")

    # ==================== Tab2 拖拽处理 ====================
    def tab2_on_interpreter_drop(self, event):
        """处理Python解释器拖放"""
        data = event.data
        if data.startswith("{") and data.endswith("}"):
            data = data[1:-1]
        elif data.startswith("file://"):
            data = unquote(data.replace("file://", ""))

        # 检查是否为可执行文件
        if os.path.isfile(data) and ("python" in data.lower() or data.endswith((".exe", ""))):
            self.tab2_interpreter_entry.delete(0, END)
            self.tab2_interpreter_entry.insert(0, data)
            self.config_data["clone_interpreter"] = data
            self.save_config()
            self.log(f"拖入Python解释器: {data}", "info")
        else:
            self.log("只支持Python解释器文件", "warning")

    def tab2_on_project_drop(self, event):
        """处理项目源码目录拖放"""
        data = event.data
        if data.startswith("{") and data.endswith("}"):
            data = data[1:-1]
        elif data.startswith("file://"):
            data = unquote(data.replace("file://", ""))

        if os.path.isdir(data):
            self.tab2_project_entry.delete(0, END)
            self.tab2_project_entry.insert(0, data)
            self.config_data["clone_project_path"] = data
            self.save_config()
            self.log(f"拖入项目源码目录: {data}", "info")
        elif data.endswith("/") or data.endswith("\\"):
            path = data.rstrip("/\\")
            if os.path.isdir(path):
                self.tab2_project_entry.delete(0, END)
                self.tab2_project_entry.insert(0, path)
                self.config_data["clone_project_path"] = path
                self.save_config()
                self.log(f"拖入项目源码目录: {path}", "info")
            else:
                self.log("路径不存在或不是文件夹", "warning")
        else:
            self.log("只支持文件夹拖放", "warning")

    def tab2_on_output_drop(self, event):
        """处理输出目录拖放"""
        data = event.data
        if data.startswith("{") and data.endswith("}"):
            data = data[1:-1]
        elif data.startswith("file://"):
            data = unquote(data.replace("file://", ""))

        if os.path.isdir(data):
            self.tab2_output_entry.delete(0, END)
            self.tab2_output_entry.insert(0, data)
            self.config_data["clone_output_path"] = data
            self.save_config()
            self.log(f"拖入输出目录: {data}", "info")
        elif data.endswith("/") or data.endswith("\\"):
            path = data.rstrip("/\\")
            if os.path.isdir(path):
                self.tab2_output_entry.delete(0, END)
                self.tab2_output_entry.insert(0, path)
                self.config_data["clone_output_path"] = path
                self.save_config()
                self.log(f"拖入输出目录: {path}", "info")
            else:
                self.log("路径不存在或不是文件夹", "warning")
        else:
            self.log("只支持文件夹拖放", "warning")

    # ==================== 标签页3: 依赖安装 ====================
    def setup_tab3_dependency(self):
        """构建依赖安装标签页"""
        main_frame = ttk.Frame(self.tab3, padding=10)
        main_frame.pack(fill=BOTH, expand=True)

        # 文件类型选择
        type_frame = ttk.LabelFrame(main_frame, text=" 分析类型 ", padding=10)
        type_frame.pack(fill=X, pady=(0, 10))

        self.tab3_input_type = tk.StringVar(value="auto")
        ttk.Radiobutton(type_frame, text="自动分析 .py 文件", variable=self.tab3_input_type, value="auto").pack(side=LEFT, padx=10)
        ttk.Radiobutton(type_frame, text="requirements.txt", variable=self.tab3_input_type, value="req").pack(side=LEFT, padx=10)
        ttk.Radiobutton(type_frame, text="pyproject.toml", variable=self.tab3_input_type, value="toml").pack(side=LEFT, padx=10)

        # 文件路径输入
        file_frame = ttk.LabelFrame(main_frame, text=" 文件路径 ", padding=10)
        file_frame.pack(fill=X, pady=(0, 10))

        self.tab3_file_entry = ttk.Entry(file_frame, font=("Microsoft YaHei UI", 10))
        self.tab3_file_entry.pack(fill=X, pady=(0, 5))
        self.tab3_file_entry.insert(0, self.config_data.get("last_import_file", ""))

        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=X)
        ttk.Button(btn_frame, text="浏览文件...", command=self.tab3_browse_file, width=15).pack(side=LEFT)
        ttk.Button(btn_frame, text="📄 定位", width=10,
                  command=lambda: locate_file(self.tab3_file_entry.get().strip())).pack(side=LEFT, padx=(10, 0))
        ttk.Button(btn_frame, text="开始检测", command=self.tab3_analyze, width=15).pack(side=LEFT, padx=(10, 0))

        # 结果显示区域
        result_frame = ttk.LabelFrame(main_frame, text=" 检测结果 ", padding=10)
        result_frame.pack(fill=BOTH, expand=True, pady=(0, 10))

        self.tab3_result_text = ScrolledText(result_frame, height=10)
        self.tab3_result_text.pack(fill=BOTH, expand=True)

        # 配置文本标签样式
        self.tab3_result_text.text.tag_config("info", foreground="blue")
        self.tab3_result_text.text.tag_config("success", foreground="#28a745")
        self.tab3_result_text.text.tag_config("error", foreground="#dc3545")
        self.tab3_result_text.text.tag_config("warning", foreground="#ffc107")

        # 按钮区域
        btn_panel = ttk.Frame(main_frame)
        btn_panel.pack()

        self.tab3_install_btn = ttk.Button(btn_panel, text="安装缺失库", command=self.tab3_install_missing, state=DISABLED, width=15)
        self.tab3_install_btn.pack(side=LEFT, padx=5)

        ttk.Button(btn_panel, text="清空", command=self.tab3_clear, width=10).pack(side=LEFT, padx=5)

        # 绑定拖放
        if DND_SUPPORT:
            file_frame.drop_target_register(DND_FILES)
            file_frame.dnd_bind('<<Drop>>', self.tab3_on_drop)
            self.tab3_file_entry.drop_target_register(DND_FILES)
            self.tab3_file_entry.dnd_bind('<<Drop>>', lambda e: self.tab3_handle_drop(e, self.tab3_file_entry))

    def tab3_browse_file(self):
        """浏览选择Python文件"""
        filepath = filedialog.askopenfilename(title="选择Python文件", filetypes=[("Python文件", "*.py"), ("所有文件", "*.*")])
        if filepath:
            self.tab3_file_entry.delete(0, END)
            self.tab3_file_entry.insert(0, filepath)
            self.tab3_analyze()

    def tab3_on_drop(self, event):
        """处理拖放"""
        data = event.data
        if data.startswith("{") and data.endswith("}"):
            data = data[1:-1]
        elif data.startswith("file://"):
            data = unquote(data.replace("file://", ""))

        if data.endswith(".py"):
            self.tab3_file_entry.delete(0, END)
            self.tab3_file_entry.insert(0, data)
            self.tab3_analyze()
        else:
            self.log("只支持.py文件", "warning")

    def tab3_handle_drop(self, event, widget):
        """处理组件拖放"""
        data = event.data
        if data.startswith("{") and data.endswith("}"):
            data = data[1:-1]
        elif data.startswith("file://"):
            data = unquote(data.replace("file://", ""))

        widget.delete(0, END)
        widget.insert(0, data)

    def tab3_analyze(self):
        """分析文件依赖"""
        import ast
        import re

        filepath = self.tab3_file_entry.get().strip()
        if not filepath:
            messagebox.showwarning("提示", "请先选择文件")
            return

        if not os.path.exists(filepath):
            messagebox.showerror("错误", f"文件不存在: {filepath}")
            return

        # 保存配置
        self.config_data["last_import_file"] = filepath
        self.save_config()

        self.missing_libs.clear()
        self.tab3_result_text.text.delete(1.0, END)
        self.tab3_install_btn.config(state=DISABLED)

        input_type = self.tab3_input_type.get()
        self.log(f"分析类型: {input_type}, 文件: {filepath}", "info")

        try:
            if input_type == "auto":
                self._analyze_py_file(filepath)
            elif input_type == "req":
                self._analyze_requirements(filepath)
            elif input_type == "toml":
                self._analyze_toml(filepath)
        except Exception as e:
            self.log(f"分析文件出错: {str(e)}", "error")

    def _analyze_py_file(self, filepath):
        """分析Python文件依赖"""
        import ast

        if not filepath.endswith('.py'):
            self.log("自动模式只支持 .py 文件", "warning")
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split('.')[0]
                    imports.add(module)
            elif isinstance(node, ast.ImportFrom) and node.module:
                module = node.module.split('.')[0]
                imports.add(module)

        for module in imports:
            if module not in self.stdlib_modules:
                if not self._check_module(module):
                    self.missing_libs.add(module)

        self._show_result()

    def _analyze_requirements(self, filepath):
        """分析requirements.txt依赖"""
        import re

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('-e'):
                continue
            pkg = re.split(r'[=<>!~]', line)[0].strip().lower()
            if pkg and not self._check_module(pkg):
                self.missing_libs.add(pkg)

        self._show_result()

    def _analyze_toml(self, filepath):
        """分析pyproject.toml依赖"""
        import re

        try:
            import toml
            with open(filepath, 'r', encoding='utf-8') as f:
                data = toml.load(f)
        except ImportError:
            try:
                import tomllib
                with open(filepath, 'rb') as f:
                    data = tomllib.load(f)
            except ImportError:
                self.log("需要安装 toml 或使用 Python 3.11+ (内置 tomllib)", "error")
                return
        except Exception as e:
            self.log(f"解析 toml 失败: {e}", "error")
            return

        dependencies = []

        # poetry 项目
        if 'tool' in data and 'poetry' in data['tool']:
            deps = data['tool']['poetry'].get('dependencies', {})
            for pkg in deps.keys():
                if pkg != 'python':
                    dependencies.append(pkg.lower())

        # pdm 项目
        if 'tool' in data and 'pdm' in data['tool']:
            deps = data['tool']['pdm'].get('dependencies', {})
            for pkg in deps.keys():
                dependencies.append(pkg.lower())

        # 标准 project.dependencies (PEP 621)
        if 'project' in data:
            deps = data['project'].get('dependencies', [])
            for dep in deps:
                pkg = re.split(r'[=<>!~\[\]]', dep)[0].strip().lower()
                if pkg:
                    dependencies.append(pkg)

        for pkg in dependencies:
            if not self._check_module(pkg):
                self.missing_libs.add(pkg)

        self._show_result()

    def _show_result(self):
        """显示分析结果"""
        if self.missing_libs:
            self.tab3_result_text.text.insert(END, f"发现 {len(self.missing_libs)} 个缺失的库:\n", "warning")
            for lib in sorted(self.missing_libs):
                self.tab3_result_text.text.insert(END, f"  - {lib}\n", "error")
            self.tab3_install_btn.config(state=NORMAL)
            self.status_var.set(f"发现 {len(self.missing_libs)} 个缺失的库")
        else:
            self.tab3_result_text.text.insert(END, "所有依赖库都已安装\n", "info")
            self.status_var.set("所有依赖库都已安装")

    def _check_module(self, module_name):
        """检查模块是否已安装"""
        return self.commander.check_module(module_name, sys.executable)

    def tab3_install_missing(self):
        """安装缺失的库"""
        if not self.missing_libs:
            return

        self.tab3_install_btn.config(state=DISABLED)
        self.status_var.set("正在安装...")

        def on_install_complete(success: int, fail: int):
            self.after(0, lambda: self.tab3_on_install_complete(success, fail))

        # 通过coordinator执行安装
        self.commander.execute_deps_install(self.missing_libs, sys.executable, on_install_complete)

    def tab3_on_install_complete(self, success: int, fail: int):
        """安装完成"""
        self.tab3_install_btn.config(state=NORMAL if self.missing_libs else DISABLED)

        if fail == 0:
            self.status_var.set(f"安装完成: {success} 个库安装成功")
            self.log(f"所有库安装完成!", "info")
        else:
            self.status_var.set(f"安装完成: {success} 成功, {fail} 失败")
            self.log(f"安装完成: {success} 成功, {fail} 失败", "warning")

    def tab3_clear(self):
        """清空"""
        self.tab3_result_text.text.delete(1.0, END)
        self.missing_libs.clear()
        self.tab3_install_btn.config(state=DISABLED)
        self.status_var.set("准备就绪")

    # ==================== 统一日志面板 ====================
    def create_log_panel(self, parent):
        """创建统一日志面板"""
        log_frame = ttk.LabelFrame(parent, text=" 执行日志 ", padding=5)
        log_frame.pack(fill=BOTH, expand=True)

        # 按钮区
        btn_frame = ttk.Frame(log_frame)
        btn_frame.pack(fill=X, pady=(0, 5))

        ttk.Button(btn_frame, text="清空日志", command=self.clear_log, width=10).pack(side=LEFT)

        # 日志文本框
        self.log_text = tk.Text(log_frame, wrap=WORD, font=("Consolas", 10), height=8)
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)

        # 滚动条
        scrollbar = ttk.Scrollbar(log_frame, orient=VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        self.update_log_colors()

    def update_log_colors(self):
        """更新日志颜色"""
        is_dark = self.config_data.get("theme", DEFAULT_THEME) == THEME_DARK
        if is_dark:
            self.log_text.config(bg="#2d2d2d", fg="#ffffff", insertbackground="white")
        else:
            self.log_text.config(bg="white", fg="black", insertbackground="black")

    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, END)

    def log(self, message, level="info"):
        """添加日志（统一方法）"""
        timestamp = time.strftime("%H:%M:%S")
        prefix = {
            "info": "[INFO]",
            "success": "[OK]",
            "error": "[ERR]",
            "warning": "[WARN]",
        }.get(level, "[*]")

        log_msg = f"[{timestamp}] {prefix} {message}\n"
        self.log_text.insert(END, log_msg)
        self.log_text.see(END)

    # ==================== 状态栏 ====================
    def create_status_bar(self, parent):
        """创建状态栏"""
        bottom_frame = ttk.Frame(parent)
        bottom_frame.pack(fill=X, pady=(10, 0))

        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(bottom_frame, textvariable=self.status_var, foreground="gray")
        status_label.pack(side=LEFT)

    # ==================== 拖拽和快捷键 ====================
    def setup_drag_and_drop(self):
        """设置拖拽"""
        try:
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self._handle_drop)
        except Exception as e:
            self.log(f"拖拽功能初始化失败: {e}", "warning")

    def _handle_drop(self, event):
        """处理拖拽事件"""
        data = event.data
        if data.startswith("{") and data.endswith("}"):
            data = data[1:-1]
        elif data.startswith("file://"):
            data = unquote(data.replace("file://", ""))

        if data.endswith(".py"):
            current_tab = self.notebook.index(self.notebook.select())
            if current_tab == 0:
                self.tab1_path_entry.delete(0, END)
                self.tab1_path_entry.insert(0, data)
                self.log(f"拖入文件: {data}", "info")
            elif current_tab == 2:
                self.tab3_file_entry.delete(0, END)
                self.tab3_file_entry.insert(0, data)
                self.tab3_analyze()
        else:
            self.log("只支持.py文件", "warning")

    # ==================== 标签页4: 便携式Python打包 ====================
    def setup_tab4_portable(self):
        """构建便携式Python打包标签页"""
        # 上下分栏
        self.paned_tab4 = ttk.PanedWindow(self.tab4, orient=VERTICAL)
        self.paned_tab4.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # 上方：选项区
        top_panel = ttk.Frame(self.paned_tab4)
        self.paned_tab4.add(top_panel, weight=3)

        # Requirements 文件选择
        req_frame = ttk.LabelFrame(top_panel, text=" Requirements 文件 ", padding=10)
        req_frame.pack(fill=X, pady=(0, 10))

        self.tab4_req_entry = ttk.Entry(req_frame, font=("Microsoft YaHei UI", 10))
        self.tab4_req_entry.pack(fill=X, pady=(0, 5))
        self.tab4_req_entry.insert(0, self.config_data.get("portable_requirements_file", ""))

        btn_frame = ttk.Frame(req_frame)
        btn_frame.pack(fill=X)

        ttk.Button(btn_frame, text="浏览文件...", command=self.tab4_browse_requirements, width=15).pack(side=LEFT)
        ttk.Button(btn_frame, text="📂 定位", command=self.tab4_locate_requirements, width=10).pack(side=LEFT, padx=(10, 0))

        # 拖拽支持
        if DND_SUPPORT:
            self.tab4_req_entry.drop_target_register(DND_FILES)
            self.tab4_req_entry.dnd_bind('<<Drop>>', lambda e: self.tab4_on_requirements_drop(e))

        # 输出目录
        output_frame = ttk.LabelFrame(top_panel, text=" 输出目录 ", padding=10)
        output_frame.pack(fill=X, pady=(0, 10))

        self.tab4_output_entry = ttk.Entry(output_frame, font=("Microsoft YaHei UI", 10))
        self.tab4_output_entry.pack(fill=X, pady=(0, 5))
        self.tab4_output_entry.insert(0, self.config_data.get("portable_output_dir", ""))

        btn_frame2 = ttk.Frame(output_frame)
        btn_frame2.pack(fill=X)

        ttk.Button(btn_frame2, text="选择文件夹...", command=self.tab4_browse_output, width=15).pack(side=LEFT)
        ttk.Button(btn_frame2, text="📂 打开", command=self.tab4_open_output, width=10).pack(side=LEFT, padx=(10, 0))

        # 拖拽支持
        if DND_SUPPORT:
            self.tab4_output_entry.drop_target_register(DND_FILES)
            self.tab4_output_entry.dnd_bind('<<Drop>>', lambda e: self.tab4_on_output_drop(e))

        # 项目设置
        project_frame = ttk.LabelFrame(top_panel, text=" 项目设置 ", padding=10)
        project_frame.pack(fill=X, pady=(0, 10))

        # 打包模式
        mode_frame = ttk.Frame(project_frame)
        mode_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(mode_frame, text="打包模式:").pack(side=LEFT)
        self.tab4_mode_var = tk.IntVar(value=self.config_data.get("portable_mode", 2))
        ttk.Radiobutton(mode_frame, text="在线模式 (从网络下载)", variable=self.tab4_mode_var, value=1).pack(side=LEFT, padx=(10, 20))
        ttk.Radiobutton(mode_frame, text="离线模式 (克隆当前环境)", variable=self.tab4_mode_var, value=2).pack(side=LEFT)

        # 应用名称
        name_frame = ttk.Frame(project_frame)
        name_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(name_frame, text="应用名称:").pack(side=LEFT)
        self.tab4_name_entry = ttk.Entry(name_frame, font=("Microsoft YaHei UI", 10), width=30)
        self.tab4_name_entry.pack(side=LEFT, padx=(10, 0))
        self.tab4_name_entry.insert(0, self.config_data.get("portable_app_name", "MyApplication"))

        # 包含项目文件
        self.tab4_include_project_var = tk.BooleanVar(value=self.config_data.get("portable_include_project", False))
        include_check = ttk.Checkbutton(project_frame, text="包含项目文件", variable=self.tab4_include_project_var,
                                       command=self.tab4_toggle_project_dir)
        include_check.pack(anchor=W, pady=(0, 10))

        # 项目目录（条件显示）
        self.tab4_project_frame = ttk.Frame(project_frame)
        self.tab4_project_frame.pack(fill=X)

        ttk.Label(self.tab4_project_frame, text="项目目录:").pack(side=LEFT)
        self.tab4_project_entry = ttk.Entry(self.tab4_project_frame, font=("Microsoft YaHei UI", 10))
        self.tab4_project_entry.pack(side=LEFT, fill=X, expand=True, padx=(10, 5))
        self.tab4_project_entry.insert(0, self.config_data.get("portable_project_dir", ""))

        ttk.Button(self.tab4_project_frame, text="选择...", command=self.tab4_browse_project, width=10).pack(side=LEFT, padx=(5, 0))

        # 拖拽支持
        if DND_SUPPORT:
            self.tab4_project_entry.drop_target_register(DND_FILES)
            self.tab4_project_entry.dnd_bind('<<Drop>>', lambda e: self.tab4_on_project_drop(e))

        # 根据配置决定是否显示项目目录
        if not self.tab4_include_project_var.get():
            self.tab4_project_frame.pack_forget()

        # 操作按钮区
        action_frame = ttk.Frame(top_panel)
        action_frame.pack(fill=X, pady=10)

        ttk.Button(action_frame, text="🚀 开始打包", command=self.tab4_execute_package, width=20).pack(side=LEFT, padx=5)
        ttk.Button(action_frame, text="❌ 取消", command=self.tab4_cancel_package, width=10).pack(side=LEFT, padx=5)

    def tab4_browse_requirements(self):
        """浏览Requirements文件"""
        file_path = filedialog.askopenfilename(
            title="选择Requirements文件",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            self.tab4_req_entry.delete(0, END)
            self.tab4_req_entry.insert(0, file_path)
            self.config_data["portable_requirements_file"] = file_path
            self.save_config()

    def tab4_locate_requirements(self):
        """定位Requirements文件"""
        req_path = self.tab4_req_entry.get()
        if req_path and Path(req_path).exists():
            open_folder(str(Path(req_path).parent))
        else:
            self.log("文件不存在", "warning")

    def tab4_browse_output(self):
        """浏览输出目录"""
        folder_path = filedialog.askdirectory(title="选择输出目录")
        if folder_path:
            self.tab4_output_entry.delete(0, END)
            self.tab4_output_entry.insert(0, folder_path)
            self.config_data["portable_output_dir"] = folder_path
            self.save_config()

    def tab4_open_output(self):
        """打开输出目录"""
        output_dir = self.tab4_output_entry.get()
        if output_dir and Path(output_dir).exists():
            open_folder(output_dir)
        else:
            self.log("目录不存在", "warning")

    def tab4_browse_project(self):
        """浏览项目目录"""
        folder_path = filedialog.askdirectory(title="选择项目目录")
        if folder_path:
            self.tab4_project_entry.delete(0, END)
            self.tab4_project_entry.insert(0, folder_path)
            self.config_data["portable_project_dir"] = folder_path
            self.save_config()

    def tab4_toggle_project_dir(self):
        """切换项目目录显示"""
        if self.tab4_include_project_var.get():
            self.tab4_project_frame.pack(fill=X)
        else:
            self.tab4_project_frame.pack_forget()
        self.config_data["portable_include_project"] = self.tab4_include_project_var.get()
        self.save_config()

    # ==================== Tab4 拖拽处理 ====================
    def tab4_on_requirements_drop(self, event):
        """处理Requirements文件拖放"""
        data = event.data
        if data.startswith("{") and data.endswith("}"):
            data = data[1:-1]
        elif data.startswith("file://"):
            data = unquote(data.replace("file://", ""))

        # 支持.txt和requirements文件
        if data.endswith((".txt", "requirements")) or "requirements" in data.lower():
            if os.path.isfile(data):
                self.tab4_req_entry.delete(0, END)
                self.tab4_req_entry.insert(0, data)
                self.config_data["portable_requirements_file"] = data
                self.save_config()
                self.log(f"拖入Requirements文件: {data}", "info")
            else:
                self.log("文件不存在", "warning")
        else:
            self.log("只支持 .txt 或 requirements 文件", "warning")

    def tab4_on_output_drop(self, event):
        """处理输出目录拖放"""
        data = event.data
        if data.startswith("{") and data.endswith("}"):
            data = data[1:-1]
        elif data.startswith("file://"):
            data = unquote(data.replace("file://", ""))

        if os.path.isdir(data):
            self.tab4_output_entry.delete(0, END)
            self.tab4_output_entry.insert(0, data)
            self.config_data["portable_output_dir"] = data
            self.save_config()
            self.log(f"拖入输出目录: {data}", "info")
        elif data.endswith("/") or data.endswith("\\"):
            path = data.rstrip("/\\")
            if os.path.isdir(path):
                self.tab4_output_entry.delete(0, END)
                self.tab4_output_entry.insert(0, path)
                self.config_data["portable_output_dir"] = path
                self.save_config()
                self.log(f"拖入输出目录: {path}", "info")
            else:
                self.log("路径不存在或不是文件夹", "warning")
        else:
            self.log("只支持文件夹拖放", "warning")

    def tab4_on_project_drop(self, event):
        """处理项目目录拖放"""
        data = event.data
        if data.startswith("{") and data.endswith("}"):
            data = data[1:-1]
        elif data.startswith("file://"):
            data = unquote(data.replace("file://", ""))

        if os.path.isdir(data):
            self.tab4_project_entry.delete(0, END)
            self.tab4_project_entry.insert(0, data)
            self.config_data["portable_project_dir"] = data
            self.save_config()
            self.log(f"拖入项目目录: {data}", "info")
        elif data.endswith("/") or data.endswith("\\"):
            path = data.rstrip("/\\")
            if os.path.isdir(path):
                self.tab4_project_entry.delete(0, END)
                self.tab4_project_entry.insert(0, path)
                self.config_data["portable_project_dir"] = path
                self.save_config()
                self.log(f"拖入项目目录: {path}", "info")
            else:
                self.log("路径不存在或不是文件夹", "warning")
        else:
            self.log("只支持文件夹拖放", "warning")

    def tab4_execute_package(self):
        """执行便携式Python打包"""
        # 验证输入
        req_file = self.tab4_req_entry.get().strip()
        output_dir = self.tab4_output_entry.get().strip()
        app_name = self.tab4_name_entry.get().strip()

        if not req_file:
            self.log("请选择 Requirements 文件", "warning")
            return

        if not Path(req_file).exists():
            self.log("Requirements 文件不存在", "error")
            return

        if not output_dir:
            self.log("请选择输出目录", "warning")
            return

        if not app_name:
            self.log("请输入应用名称", "warning")
            return

        if self.is_processing:
            self.log("已有打包任务在进行中", "warning")
            return

        # 保存配置
        self.config_data["portable_requirements_file"] = req_file
        self.config_data["portable_output_dir"] = output_dir
        self.config_data["portable_mode"] = self.tab4_mode_var.get()
        self.config_data["portable_app_name"] = app_name
        self.config_data["portable_include_project"] = self.tab4_include_project_var.get()
        self.config_data["portable_project_dir"] = self.tab4_project_entry.get()
        self.save_config()

        # 标记处理中
        self.is_processing = True

        # 获取项目目录
        project_dir = None
        if self.tab4_include_project_var.get():
            project_dir = self.tab4_project_entry.get().strip()
            if not project_dir or not Path(project_dir).exists():
                self.log("项目目录无效", "error")
                self.is_processing = False
                return

        # 执行打包
        def on_complete(success: bool, result: str):
            self.is_processing = False
            if success:
                self.log(f"✓ 打包完成: {result}", "info")
                self.log("打包文件已保存到 dist 目录", "info")
            else:
                self.log(f"✗ 打包失败: {result}", "error")

        self.log("开始执行便携式Python打包...", "info")
        self.commander.execute_portable_package(
            requirements_file=req_file,
            output_dir=output_dir,
            mode=self.tab4_mode_var.get(),
            include_project=self.tab4_include_project_var.get(),
            project_dir=project_dir,
            app_name=app_name,
            on_complete=on_complete
        )

    def tab4_cancel_package(self):
        """取消打包（预留）"""
        if self.is_processing:
            self.log("正在尝试取消打包...", "warning")
        else:
            self.log("当前没有正在进行的打包任务", "info")

    def bind_shortcuts(self):
        """绑定快捷键"""
        self.bind("<Command-s>", lambda e: self.save_config())
        self.bind("<Control-s>", lambda e: self.save_config())
        self.bind("<Command-q>", lambda e: self.quit())
        self.bind("<Control-q>", lambda e: self.quit())
