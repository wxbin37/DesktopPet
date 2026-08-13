#!/usr/bin/env python3
"""
桌宠主程序入口
综合了 BongoCat 键盘互动 + OnePic 多状态动画 的桌面宠物
"""
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from pet_window import PetWindow


def _get_smoke_test_ms(argv):
    for arg in argv[1:]:
        if arg.startswith("--smoke-test-ms="):
            try:
                return max(0, int(arg.split("=", 1)[1]))
            except ValueError:
                return 0
    return 0


def main():
    smoke_test_ms = _get_smoke_test_ms(sys.argv)

    # 高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("DesktopPetGirl")
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出（托盘运行）
    
    # 设置默认字体
    font = QFont("PingFang SC" if sys.platform == "darwin" else "Microsoft YaHei", 9)
    app.setFont(font)
    
    # 创建桌宠窗口
    pet = PetWindow(keyboard_enabled=not smoke_test_ms)
    pet.show()

    if smoke_test_ms:
        QTimer.singleShot(250, lambda: pet._trigger_bongo_tap("kc:0"))
        QTimer.singleShot(500, lambda: pet._trigger_bongo_tap("kc:4"))
        QTimer.singleShot(750, pet._show_keyboard_status)
        QTimer.singleShot(smoke_test_ms, pet._quit)
    
    print("桌宠已启动！")
    print("- 只有点到桌宠本体才会互动，空白透明区域不挡页面")
    print("- 左键拖拽移动，松手后会在原地附近活动")
    print("- 右键桌宠或菜单栏图标可切换状态、设置或退出")
    print("- 打字时会同步打字状态")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
