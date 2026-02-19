# ==================== 程序入口 ====================
"""程序入口模块"""

import sys
from pathlib import Path

# 确保src目录在路径中
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def main():
    """程序入口"""
    from l2_gui import MainWindow

    app = MainWindow()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
