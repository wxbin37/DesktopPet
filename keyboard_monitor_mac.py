"""
macOS 原生键盘监听器 - 用 ctypes 直接调用 Quartz 框架
不依赖 pyobjc / pynput
"""
import time
import threading
from ctypes import *
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from config import TYPING_TIMEOUT


# 加载 Quartz 框架
quartz = cdll.LoadLibrary('/System/Library/Frameworks/Quartz.framework/Quartz')

# 定义常量
kCGEventMaskForAllEvents = (1 << 28) - 1
kCGEventKeyDown = 10
kCGEventKeyUp = 11
kCGEventFlagsChanged = 12

kCFRunLoopRunFinished = 1
kCFRunLoopRunStopped = 2
kCFRunLoopRunTimedOut = 3
kCFRunLoopRunHandledSource = 4

kCFRunLoopDefaultMode = c_void_p.in_dll(quartz, 'kCFRunLoopDefaultMode')

# 类型定义
CGEventRef = c_void_p
CGEventTapProxy = c_void_p
CGEventMask = c_uint64
CGEventTapLocation = c_uint32
CGEventTapOptions = c_uint32
CGEventTapPlacement = c_uint32
CFIndex = c_long
CFMachPortRef = c_void_p

kCGHeadInsertEventTap = 0
kCGTailAppendEventTap = 1

kCGEventTapOptionDefault = 0x00000000
kCGEventTapOptionListenOnly = 0x00000001

# 函数原型
CGEventTapCreate = quartz.CGEventTapCreate
CGEventTapCreate.argtypes = [
    CGEventTapLocation,  # tap
    CGEventTapPlacement,  # place
    CGEventTapOptions,  # options
    CGEventMask,  # eventsOfInterest
    c_void_p,  # callback
    c_void_p,  # userInfo
]
CGEventTapCreate.restype = c_void_p

CGEventTapEnable = quartz.CGEventTapEnable
CGEventTapEnable.argtypes = [c_void_p, c_bool]

CGEventGetIntegerValueField = quartz.CGEventGetIntegerValueField
CGEventGetIntegerValueField.argtypes = [CGEventRef, c_uint32]
CGEventGetIntegerValueField.restype = c_int64
kCGKeyboardEventKeycode = 9

try:
    CGPreflightListenEventAccess = quartz.CGPreflightListenEventAccess
    CGPreflightListenEventAccess.argtypes = []
    CGPreflightListenEventAccess.restype = c_bool

    CGRequestListenEventAccess = quartz.CGRequestListenEventAccess
    CGRequestListenEventAccess.argtypes = []
    CGRequestListenEventAccess.restype = c_bool
except AttributeError:
    CGPreflightListenEventAccess = None
    CGRequestListenEventAccess = None

CFRunLoopGetCurrent = quartz.CFRunLoopGetCurrent
CFRunLoopGetCurrent.restype = c_void_p

CFRunLoopAddSource = quartz.CFRunLoopAddSource
CFRunLoopAddSource.argtypes = [c_void_p, c_void_p, c_void_p]

CFRunLoopRun = quartz.CFRunLoopRun
CFRunLoopRun.restype = c_int32

CFRunLoopStop = quartz.CFRunLoopStop
CFRunLoopStop.argtypes = [c_void_p]

CFMachPortCreateRunLoopSource = quartz.CFMachPortCreateRunLoopSource
CFMachPortCreateRunLoopSource.argtypes = [c_void_p, c_void_p, CFIndex]
CFMachPortCreateRunLoopSource.restype = c_void_p

# 回调函数类型
CGEventTapCallBack = CFUNCTYPE(
    CGEventRef,  # return
    CGEventTapProxy,  # proxy
    c_uint32,  # type
    CGEventRef,  # event
    c_void_p,  # userinfo
)


class MacKeyboardMonitor(QObject):
    """
    macOS 原生键盘监听器
    """
    typing_started = pyqtSignal()
    typing_stopped = pyqtSignal()
    key_pressed = pyqtSignal(str)
    monitor_started = pyqtSignal(str)
    monitor_failed = pyqtSignal(str)
    key_released = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.is_typing = False
        self.last_key_time = 0
        self.run_loop = None
        self.tap = None
        self.listener_thread = None
        self._running = False
        self.last_error = ""
        
        # 超时检测定时器
        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self._check_typing_timeout)
        self.key_pressed.connect(self._handle_key_pressed)
        
        # 回调函数
        self._callback = CGEventTapCallBack(self._event_callback)
    
    def _event_callback(self, proxy, type_, event, userinfo):
        """事件回调"""
        if type_ == kCGEventKeyDown:
            keycode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
            self.key_pressed.emit(f"kc:{keycode}")
        elif type_ == kCGEventKeyUp:
            keycode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
            self.key_released.emit(f"kc:{keycode}")
        
        return event
    
    def _handle_key_pressed(self, key):
        """在 Qt 主线程中处理按键，确保计时器稳定工作。"""
        current_time = time.time() * 1000

        if not self.is_typing:
            self.is_typing = True
            self.typing_started.emit()

        self.last_key_time = current_time
        self.timeout_timer.start(TYPING_TIMEOUT)

    def _ensure_input_monitoring_permission(self):
        """触发 macOS 输入监控授权；无授权时全局打字动画无法工作。"""
        if not CGPreflightListenEventAccess or not CGRequestListenEventAccess:
            return True

        if CGPreflightListenEventAccess():
            self.last_error = ""
            return True

        print("正在请求 macOS 输入监控权限，用于桌宠跟随键盘打字")
        granted = CGRequestListenEventAccess()
        if not granted and not CGPreflightListenEventAccess():
            self.last_error = "未获得 macOS 输入监控权限"
            print(f"提示: {self.last_error}，键盘打字动画暂时不可用")
            return False
        self.last_error = ""
        return True
    
    def start(self):
        """启动键盘监听"""
        if self._running:
            return True

        if not self._ensure_input_monitoring_permission():
            self.monitor_failed.emit(self.last_error or "未获得 macOS 输入监控权限")
            return False
        
        self._running = True
        self.listener_thread = threading.Thread(target=self._run_listener, daemon=True)
        self.listener_thread.start()
        return True
    
    def _run_listener(self):
        """监听线程"""
        try:
            # 优先使用低层 HID tap；如果权限或系统限制失败，再退到 session tap。
            self.tap = None
            tap_name = ""
            for tap_location, candidate_name in [(0, "HID"), (1, "Session")]:
                self.tap = CGEventTapCreate(
                    tap_location,
                    kCGHeadInsertEventTap,
                    kCGEventTapOptionListenOnly,
                    (1 << kCGEventKeyDown) | (1 << kCGEventKeyUp),
                    self._callback,
                    None
                )
                if self.tap:
                    tap_name = candidate_name
                    break
            
            if not self.tap:
                self.last_error = "无法创建键盘监听，请在输入监控中授权 DesktopPet.app"
                print(f"警告: {self.last_error}")
                print("键盘互动功能将不可用，但桌宠其他功能正常")
                self._running = False
                self.monitor_failed.emit(self.last_error)
                return
            
            # 创建 run loop source
            runloop_source = CFMachPortCreateRunLoopSource(
                None, self.tap, 0
            )
            
            self.run_loop = CFRunLoopGetCurrent()
            CFRunLoopAddSource(self.run_loop, runloop_source, kCFRunLoopDefaultMode)
            
            CGEventTapEnable(self.tap, True)
            self.last_error = ""
            self.monitor_started.emit(f"键盘监听已启动: {tap_name} tap")
            
            CFRunLoopRun()
        except Exception as e:
            self.last_error = f"键盘监听启动失败: {e}"
            self._running = False
            print(self.last_error)
            self.monitor_failed.emit(self.last_error)
    
    def stop(self):
        """停止键盘监听"""
        self._running = False
        self.timeout_timer.stop()
        
        if self.run_loop:
            try:
                CFRunLoopStop(self.run_loop)
            except:
                pass
    
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
