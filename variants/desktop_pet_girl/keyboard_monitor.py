"""
键盘监听器 - 全局监听键盘输入，触发打字状态
"""
import time
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from pynput import keyboard
from config import TYPING_TIMEOUT


class KeyboardMonitor(QObject):
    # 信号：开始打字
    typing_started = pyqtSignal()
    # 信号：停止打字
    typing_stopped = pyqtSignal()
    # 信号：按键事件（用于特殊按键检测）
    key_pressed = pyqtSignal(str)
    key_released = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.is_typing = False
        self.last_key_time = 0
        self.listener = None
        
        # 超时检测定时器
        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self._check_typing_timeout)
    
    def start(self):
        """启动键盘监听"""
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.daemon = True
        self.listener.start()
        return True
    
    def stop(self):
        """停止键盘监听"""
        if self.listener:
            self.listener.stop()
            self.listener = None
        self.timeout_timer.stop()
    
    def _on_press(self, key):
        """按键按下事件"""
        current_time = time.time() * 1000  # 转为ms
        
        # 检测是否开始新的打字会话
        if not self.is_typing:
            self.is_typing = True
            self.typing_started.emit()
        
        self.last_key_time = current_time
        
        # 重置超时计时器
        self.timeout_timer.start(TYPING_TIMEOUT)
        
        # 发送按键信号
        try:
            key_str = key.char if hasattr(key, 'char') and key.char else str(key)
            self.key_pressed.emit(key_str)
        except AttributeError:
            self.key_pressed.emit(str(key))
    
    def _on_release(self, key):
        """按键释放事件"""
        try:
            key_str = key.char if hasattr(key, 'char') and key.char else str(key)
            self.key_released.emit(key_str)
        except AttributeError:
            self.key_released.emit(str(key))
    
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
