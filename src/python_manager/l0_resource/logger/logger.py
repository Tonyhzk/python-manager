# ==================== 日志系统 ====================
"""日志系统实现"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import sys


class Logger:
    """日志器"""

    def __init__(self, log_dir: str = "logs", level: str = "INFO"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.level = getattr(logging, level.upper(), logging.INFO)
        self.logger = logging.getLogger("PythonManager")
        self.logger.setLevel(self.level)
        self._setup_handlers()

    def _setup_handlers(self):
        """设置处理器"""
        if not self.logger.handlers:
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.level)
            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] %(message)s",
                datefmt="%H:%M:%S"
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            # 文件处理器
            log_file = self.log_dir / f"python_manager_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(self.level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def info(self, message: str):
        """INFO级别日志"""
        self.logger.info(message)

    def error(self, message: str):
        """ERROR级别日志"""
        self.logger.error(message)

    def debug(self, message: str):
        """DEBUG级别日志"""
        self.logger.debug(message)

    def warning(self, message: str):
        """WARNING级别日志"""
        self.logger.warning(message)


# 全局日志实例
_log_instance: Optional[Logger] = None


def init_logger(log_dir: str = "logs", level: str = "INFO") -> Logger:
    """初始化日志系统"""
    global _log_instance
    _log_instance = Logger(log_dir=log_dir, level=level)
    return _log_instance


def get_logger() -> Logger:
    """获取日志实例"""
    global _log_instance
    if _log_instance is None:
        _log_instance = Logger()
    return _log_instance


def info(message: str):
    """快捷INFO日志"""
    get_logger().info(message)


def error(message: str):
    """快捷ERROR日志"""
    get_logger().error(message)


def debug(message: str):
    """快捷DEBUG日志"""
    get_logger().debug(message)


def warning(message: str):
    """快捷WARNING日志"""
    get_logger().warning(message)
