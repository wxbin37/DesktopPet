"""Windows/Linux 全局键盘监听器。

``pynput`` 的回调运行在后台线程。所有 Qt 状态和计时器都通过内部信号
切回主线程处理，避免 Windows 上出现计时器失效、打字状态不结束或程序
随机卡住的问题。监听器只读取按键事件，不会模拟输入或抢占输入焦点。
"""
import time
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from pynput import keyboard
from config import TYPING_TIMEOUT


class KeyboardMonitor(QObject):
    typing_started = pyqtSignal()
    typing_stopped = pyqtSignal()
    key_pressed = pyqtSignal(str)
    key_released = pyqtSignal(str)
    monitor_started = pyqtSignal(str)
    monitor_failed = pyqtSignal(str)

    # pynput 回调线程 -> Qt 主线程
    _raw_key_pressed = pyqtSignal(str)
    _raw_key_released = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.is_typing = False
        self.last_key_time = 0
        self.listener = None
        self.last_error = ""

        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self._check_typing_timeout)

        self._raw_key_pressed.connect(self._process_press)
        self._raw_key_released.connect(self._process_release)

    def start(self):
        """启动键盘监听"""
        if self.listener:
            return True

        try:
            self.listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release,
            )
            self.listener.daemon = True
            self.listener.start()
            self.last_error = ""
            self.monitor_started.emit("Windows 键盘监听已启动")
            return True
        except Exception as exc:
            self.listener = None
            self.last_error = f"键盘监听启动失败: {exc}"
            self.monitor_failed.emit(self.last_error)
            return False

    def stop(self):
        """停止键盘监听"""
        if self.listener:
            self.listener.stop()
            self.listener = None
        self.timeout_timer.stop()

    @staticmethod
    def _key_text(key):
        try:
            return key.char if hasattr(key, "char") and key.char else str(key)
        except (AttributeError, TypeError):
            return str(key)

    def _on_press(self, key):
        """pynput 后台线程中的按下回调。"""
        self._raw_key_pressed.emit(self._key_text(key))

    def _on_release(self, key):
        """pynput 后台线程中的松开回调。"""
        self._raw_key_released.emit(self._key_text(key))

    def _process_press(self, key_text):
        """在 Qt 主线程处理按下事件和计时器。"""
        current_time = time.time() * 1000

        if not self.is_typing:
            self.is_typing = True
            self.typing_started.emit()

        self.last_key_time = current_time
        self.timeout_timer.start(TYPING_TIMEOUT)
        self.key_pressed.emit(key_text)

    def _process_release(self, key_text):
        """在 Qt 主线程转发松开事件。"""
        self.key_released.emit(key_text)

    def _check_typing_timeout(self):
        """检查打字是否超时"""
        current_time = time.time() * 1000
        if current_time - self.last_key_time >= TYPING_TIMEOUT:
            if self.is_typing:
                self.is_typing = False
                self.typing_stopped.emit()

    def is_active(self):
        """是否正在打字"""
        return self.is_typing
