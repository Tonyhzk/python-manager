# ==================== 应用常量 ====================
from pathlib import Path
import sys
import platform

# ========== 基础配置 ==========
APP_NAME = "HZK Python管理"
APP_FOLDER_NAME = "HZKPythonManager"
APP_VERSION = "v3.0.0"

# ========== 窗口设置 ==========
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 950
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 950

# ========== 主题设置 ==========
DEFAULT_THEME = "darkly"
THEME_LIGHT = "litera"
THEME_DARK = "darkly"

# ========== 文件设置 ==========
CONFIG_FILE_NAME = "python_manager_config.json"
LOG_FILE_NAME = "python_manager.log"

# ========== 资源文件夹 ==========
RESOURCES_FOLDER = "res"

# ========== 颜色配置 ==========
COLOR_SUCCESS = "#28a745"
COLOR_WARNING = "#ffc107"
COLOR_ERROR = "#dc3545"


def get_base_path() -> Path:
    """获取程序基础路径（兼容打包状态）"""
    if getattr(sys, 'frozen', False) or getattr(sys, '_MEIPASS', False):
        if hasattr(sys, '_MEIPASS'):
            return Path(sys._MEIPASS)
        return Path(sys.executable).parent
    return Path(__file__).parent.parent.parent.parent


def get_config_dir() -> Path:
    """获取配置目录"""
    if getattr(sys, 'frozen', False):
        if platform.system() == "Darwin":
            return Path.home() / "Library" / "Application Support" / APP_FOLDER_NAME
        return Path(sys.executable).parent
    return Path(__file__).parent.parent.parent


def get_config_path() -> Path:
    """获取配置文件路径"""
    return get_config_dir() / CONFIG_FILE_NAME


def get_dist_path() -> Path:
    """获取打包输出目录"""
    return get_base_path() / "dist"
