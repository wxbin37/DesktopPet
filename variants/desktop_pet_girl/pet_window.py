"""
桌宠主窗口
"""
import sys
import os
from PyQt6.QtWidgets import QApplication, QLabel, QMenu, QSystemTrayIcon, QVBoxLayout, QWidget
from PyQt6.QtGui import (
    QAction, QBrush, QColor, QDesktopServices, QIcon, QImage, QMouseEvent,
    QFont, QPainter, QPen, QPixmap, QPolygonF, QRegion, QTransform
)
from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF, QTimer, QUrl
from PyQt6.QtGui import QGuiApplication

import platform
from animation_manager import AnimationManager
from mac_window_utils import apply_strong_topmost, set_ignores_mouse_events
from state_machine import StateMachine
from config import (
    BONGO_KEY_HOLD_MS, BONGO_TAP_RELEASE_MS,
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_OPACITY, ALWAYS_ON_TOP,
    CLICK_ALPHA_THRESHOLD, MOUSE_INTERACTION_ENABLED, PetState, WALK_RANGE,
    TYPING_TIMEOUT, WALK_SPEED, DEFAULT_CHARACTER, resource_path
)


IS_MAC = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"


MAC_KEYCODE_TO_KEY_ID = {
    0: "A", 1: "S", 2: "D", 3: "F", 4: "H", 5: "G", 6: "Z", 7: "X",
    8: "C", 9: "V", 11: "B", 12: "Q", 13: "W", 14: "E", 15: "R",
    16: "Y", 17: "T", 18: "1", 19: "2", 20: "3", 21: "4", 22: "6",
    23: "5", 24: "=", 25: "9", 26: "7", 27: "-", 28: "8", 29: "0",
    30: "]", 31: "O", 32: "U", 33: "[", 34: "I", 35: "P",
    36: "ENTER", 37: "L", 38: "J", 39: "'", 40: "K", 41: ";",
    42: "\\", 43: ",", 44: "/", 45: "N", 46: "M", 47: ".",
    48: "TAB", 49: "SPACE", 50: "`", 51: "DEL", 53: "ESC",
    55: "CMD", 56: "SHIFT", 57: "CAPS", 58: "OPT", 59: "CTRL",
    60: "SHIFT_R", 61: "OPT_R", 62: "CTRL_R", 76: "ENTER",
    123: "LEFT", 124: "RIGHT", 125: "DOWN", 126: "UP",
}

KEYBOARD_ROWS = [
    [("ESC", 1.0), ("`", 1.0), ("1", 1.0), ("2", 1.0), ("3", 1.0), ("4", 1.0),
     ("5", 1.0), ("6", 1.0), ("7", 1.0), ("8", 1.0), ("9", 1.0), ("0", 1.0),
     ("-", 1.0), ("=", 1.0), ("DEL", 1.45)],
    [("TAB", 1.45), ("Q", 1.0), ("W", 1.0), ("E", 1.0), ("R", 1.0), ("T", 1.0),
     ("Y", 1.0), ("U", 1.0), ("I", 1.0), ("O", 1.0), ("P", 1.0), ("[", 1.0),
     ("]", 1.0), ("\\", 1.25)],
    [("CAPS", 1.75), ("A", 1.0), ("S", 1.0), ("D", 1.0), ("F", 1.0), ("G", 1.0),
     ("H", 1.0), ("J", 1.0), ("K", 1.0), ("L", 1.0), (";", 1.0), ("'", 1.0),
     ("ENTER", 1.9)],
    [("SHIFT", 2.15), ("Z", 1.0), ("X", 1.0), ("C", 1.0), ("V", 1.0), ("B", 1.0),
     ("N", 1.0), ("M", 1.0), (",", 1.0), (".", 1.0), ("/", 1.0), ("SHIFT_R", 2.25)],
    (
        [("CTRL", 1.25), ("WIN", 1.25), ("ALT", 1.35), ("SPACE", 5.7),
         ("ALT_R", 1.35), ("WIN_R", 1.25), ("LEFT", 1.0), ("DOWN", 1.0),
         ("UP", 1.0), ("RIGHT", 1.0)]
        if IS_WINDOWS
        else [("CTRL", 1.25), ("OPT", 1.25), ("CMD", 1.35), ("SPACE", 5.7),
              ("CMD_R", 1.35), ("OPT_R", 1.25), ("LEFT", 1.0), ("DOWN", 1.0),
              ("UP", 1.0), ("RIGHT", 1.0)]
    ),
]

KEY_DISPLAY_LABELS = {
    "ESC": "esc",
    "TAB": "⇥",
    "CAPS": "caps",
    "DEL": "⌫",
    "ENTER": "↩",
    "SHIFT": "⇧",
    "SHIFT_R": "⇧",
    "CMD": "⌘",
    "CMD_R": "⌘",
    "OPT": "⌥",
    "OPT_R": "⌥",
    "CTRL": "Ctrl" if IS_WINDOWS else "⌃",
    "CTRL_R": "Ctrl" if IS_WINDOWS else "⌃",
    "WIN": "Win",
    "WIN_R": "Win",
    "ALT": "Alt",
    "ALT_R": "Alt",
    "SPACE": "space",
    "LEFT": "←",
    "RIGHT": "→",
    "UP": "↑",
    "DOWN": "↓",
}

# 根据平台导入键盘监听器
if platform.system() == 'Darwin':
    try:
        from keyboard_monitor_mac import MacKeyboardMonitor as KeyboardMonitor
        KEYBOARD_MONITOR_AVAILABLE = True
    except ImportError:
        KEYBOARD_MONITOR_AVAILABLE = False
else:
    try:
        from keyboard_monitor import KeyboardMonitor
        KEYBOARD_MONITOR_AVAILABLE = True
    except ImportError:
        KEYBOARD_MONITOR_AVAILABLE = False


class PetWindow(QWidget):
    def __init__(self, keyboard_enabled=True):
        super().__init__()
        
        # 窗口设置
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |  # 无边框
            Qt.WindowType.WindowStaysOnTopHint |  # 始终置顶
            Qt.WindowType.Tool |  # 任务栏不显示
            Qt.WindowType.WindowDoesNotAcceptFocus |
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # 透明背景
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            not MOUSE_INTERACTION_ENABLED,
        )
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setWindowOpacity(WINDOW_OPACITY)
        
        # 窗口大小
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # 位置初始化（屏幕右下角）
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - WINDOW_WIDTH - 50, 
                  screen.height() - WINDOW_HEIGHT - 50)
        
        # 拖拽相关
        self.dragging = False
        self.drag_position = QPoint()
        self.home_position = QPoint(self.x(), self.y())
        self._mask_cache = {}
        self._last_click_mask_signature = None

        # BongoCat 风格敲击键盘视觉状态
        self.bongo_pressed = False
        self.left_hand_down = False
        self.left_hand_tap_phase = 0
        self.left_hand_tap_token = 0
        self.active_keys = {}
        self.held_keys = set()
        self.key_release_tokens = {}
        self.last_keyboard_key = ""
        self.bongo_release_timer = QTimer()
        self.bongo_release_timer.setSingleShot(True)
        self.bongo_release_timer.timeout.connect(self._release_bongo_tap)
        self.left_hand_tap_timer = QTimer()
        self.left_hand_tap_timer.setSingleShot(True)
        self.left_hand_tap_timer.timeout.connect(self._release_left_hand_tap)
        self.typing_idle_timer = QTimer()
        self.typing_idle_timer.setSingleShot(True)
        self.typing_idle_timer.timeout.connect(self._on_typing_idle_timeout)
        self.keyboard_status = "未启动"
        self.real_key_count = 0
        self.last_real_key = "无"
        self.status_popup = None
        self.typing_scene_base = QPixmap(
            resource_path("assets", DEFAULT_CHARACTER, "typing_mongocat_base.png")
        )
        self.typing_scene_tap = QPixmap(
            resource_path("assets", DEFAULT_CHARACTER, "typing_mongocat_tap.png")
        )
        self.typing_rest_overlay = QPixmap(
            resource_path("assets", DEFAULT_CHARACTER, "typing_mongocat_rest_overlay.png")
        )
        self.typing_tap_overlay = QPixmap(
            resource_path("assets", DEFAULT_CHARACTER, "typing_mongocat_tap_overlay.png")
        )
        
        # 动画管理器
        self.animation = AnimationManager()
        self.animation.on_frame_changed = self._on_animation_frame_changed
        self.animation.start()
        
        # 状态机
        self.state_machine = StateMachine()
        self.state_machine.state_changed.connect(self._on_state_changed)
        self.state_machine.walk_requested.connect(self._on_walk_step)
        self.state_machine.start()
        
        # 键盘监听器
        self.keyboard_monitor = None
        self.keyboard_available = bool(keyboard_enabled and KEYBOARD_MONITOR_AVAILABLE)
        if self.keyboard_available:
            try:
                self.keyboard_monitor = KeyboardMonitor()
                self.keyboard_monitor.key_pressed.connect(self._on_key_pressed)
                if hasattr(self.keyboard_monitor, "key_released"):
                    self.keyboard_monitor.key_released.connect(self._on_key_released)
                self.keyboard_monitor.typing_started.connect(self._on_typing_start)
                self.keyboard_monitor.typing_stopped.connect(self._on_typing_stop)
                if hasattr(self.keyboard_monitor, "monitor_failed"):
                    self.keyboard_monitor.monitor_failed.connect(self._on_keyboard_monitor_failed)
                if hasattr(self.keyboard_monitor, "monitor_started"):
                    self.keyboard_monitor.monitor_started.connect(self._on_keyboard_monitor_started)
                started = self.keyboard_monitor.start()
                if started:
                    self.keyboard_status = "已启动，等待按键"
                else:
                    self.keyboard_status = getattr(
                        self.keyboard_monitor,
                        "last_error",
                        "键盘监听启动失败",
                    )
                    self.keyboard_available = False
            except Exception as e:
                print(f"键盘监听初始化失败: {e}")
                if IS_MAC:
                    print("提示: macOS 需要在 系统设置 > 隐私与安全性 > 输入监控 中授权应用")
                else:
                    print("提示: 请检查安全软件是否阻止了桌宠的全局键盘监听")
                self.keyboard_status = f"键盘监听初始化失败: {e}"
                self.keyboard_available = False
        else:
            print("提示: 键盘监听功能不可用，打字互动将无法触发")
            print("      你仍可以通过菜单栏图标手动切换状态")
            self.keyboard_status = "键盘监听功能不可用"
        
        # 系统托盘
        self._init_tray()
        
        # 走路边界检测
        self.screen_geometry = screen

        # 使用当前系统的原生方式再设置一次窗口层级。
        # 不能反复 raise 窗口，否则会打断中文输入法候选框。
        QTimer.singleShot(0, self._ensure_topmost)
        QTimer.singleShot(500, self._ensure_topmost)
        QTimer.singleShot(0, self._update_click_mask)
    
    def _init_tray(self):
        """初始化系统托盘"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # 使用第一帧作为托盘图标
        first_frame = self.animation.get_current_frame()
        if first_frame:
            self.tray_icon.setIcon(QIcon(first_frame))
        
        # 托盘菜单
        tray_menu = QMenu()
        
        show_action = QAction("显示/隐藏", self)
        show_action.triggered.connect(self._toggle_visible)
        tray_menu.addAction(show_action)
        
        reset_action = QAction("重置位置", self)
        reset_action.triggered.connect(self._reset_position)
        tray_menu.addAction(reset_action)

        if IS_MAC:
            permission_action = QAction("打开输入监控设置", self)
            permission_action.triggered.connect(self._open_input_monitoring_settings)
            tray_menu.addAction(permission_action)

        test_bongo_action = QAction("测试真实键位动画", self)
        test_bongo_action.triggered.connect(self._test_bongo_tap)
        tray_menu.addAction(test_bongo_action)

        keyboard_status_action = QAction("查看键盘监听状态", self)
        keyboard_status_action.triggered.connect(self._show_keyboard_status)
        tray_menu.addAction(keyboard_status_action)
        
        tray_menu.addSeparator()
        
        # 状态切换子菜单
        state_menu = tray_menu.addMenu("切换状态")
        
        idle_action = QAction("待机", self)
        idle_action.triggered.connect(lambda: self.state_machine.request_state(PetState.IDLE, True))
        state_menu.addAction(idle_action)
        
        happy_action = QAction("开心", self)
        happy_action.triggered.connect(lambda: self.state_machine.request_state(PetState.HAPPY, True))
        state_menu.addAction(happy_action)
        
        sleep_action = QAction("睡觉", self)
        sleep_action.triggered.connect(lambda: self.state_machine.request_state(PetState.SLEEPING, True))
        state_menu.addAction(sleep_action)
        
        walk_action = QAction("走路", self)
        walk_action.triggered.connect(lambda: self.state_machine.request_state(PetState.WALKING, True))
        state_menu.addAction(walk_action)

        surprised_action = QAction("惊讶", self)
        surprised_action.triggered.connect(lambda: self.state_machine.request_state(PetState.SURPRISED, True))
        state_menu.addAction(surprised_action)

        wakeup_action = QAction("醒来", self)
        wakeup_action.triggered.connect(lambda: self.state_machine.request_state(PetState.WAKEUP, True))
        state_menu.addAction(wakeup_action)

        selfie_action = QAction("自拍", self)
        selfie_action.triggered.connect(lambda: self.state_machine.request_state(PetState.SELFIE, True))
        state_menu.addAction(selfie_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self._quit)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("桌宠")
        self.tray_icon.show()
    
    def _on_state_changed(self, state):
        """状态改变回调"""
        self.animation.set_state(state)
        self._update_click_mask()
        self.update()
    
    def _on_typing_start(self):
        """开始打字"""
        self.state_machine.notify_activity()
        self.state_machine.request_state(PetState.TYPING)

    def _on_key_pressed(self, key):
        """BongoCat 风格：每次按键立即敲一下键盘。"""
        self.real_key_count += 1
        self.last_real_key = key
        key_id = self._key_to_keyboard_key(key)
        self.keyboard_status = f"收到按键: {KEY_DISPLAY_LABELS.get(key_id, key_id) or key}"
        self._trigger_bongo_tap(key, hold_until_keyup=True)

    def _on_key_released(self, key):
        """真实按键松开后，释放对应键位高亮。"""
        key_id = self._key_to_keyboard_key(key)
        if key_id:
            self.held_keys.discard(key_id)
            self._schedule_key_release(key_id, 40)

    def _trigger_bongo_tap(self, key, hold_until_keyup=False):
        """触发一次 BongoCat 风格敲击动画，可来自真实按键或测试。"""
        self.state_machine.notify_activity()
        self.state_machine.request_state(PetState.TYPING)

        key_id = self._key_to_keyboard_key(key)
        if key_id:
            self.active_keys[key_id] = True
            self.last_keyboard_key = key_id
            if hold_until_keyup:
                self.held_keys.add(key_id)
            else:
                self._schedule_key_release(key_id, BONGO_KEY_HOLD_MS)

        self.bongo_pressed = True
        self._start_left_hand_tap_pulse()

        # 保留按键节奏，但打字姿势由 mongocat 底图和左手覆盖层负责。
        self.animation.set_frame(1)
        self.bongo_release_timer.start(BONGO_TAP_RELEASE_MS)
        self.typing_idle_timer.start(TYPING_TIMEOUT)
        self.update()

    def _start_left_hand_tap_pulse(self):
        """每次真实按键都制造一次清楚的“抬起—敲下”左手节奏。"""
        self.left_hand_tap_token += 1
        token = self.left_hand_tap_token

        if self.left_hand_tap_phase:
            # 连续快速输入时，先短暂回到休息帧，否则手会一直粘在键盘上。
            self.left_hand_tap_phase = 0
            self._refresh_hand_down_state()
            self.update()
            QTimer.singleShot(28, lambda t=token: self._press_left_hand_tap(t))
            return

        self._press_left_hand_tap(token)

    def _press_left_hand_tap(self, token):
        """进入左手下压帧，并在短时间后弹回。"""
        if token != self.left_hand_tap_token:
            return

        self.left_hand_tap_phase = 1
        self._refresh_hand_down_state()
        self.left_hand_tap_timer.start(95)
        self.update()

    def _schedule_key_release(self, key_id, delay_ms):
        """短暂延迟释放键位，避免高亮闪得太快看不清。"""
        token = self.key_release_tokens.get(key_id, 0) + 1
        self.key_release_tokens[key_id] = token
        QTimer.singleShot(delay_ms, lambda k=key_id, t=token: self._release_keyboard_key(k, t))

    def _release_keyboard_key(self, key_id, token):
        if self.key_release_tokens.get(key_id) != token:
            return
        if key_id in self.held_keys:
            return
        self.active_keys.pop(key_id, None)
        self._refresh_hand_down_state()
        self.update()
    
    def _on_typing_stop(self):
        """停止打字"""
        self.keyboard_status = "已停止打字，等待按键"
        self._finish_typing_state()

    def _on_typing_idle_timeout(self):
        """兜底：只要一段时间没有按键，就退出敲键盘状态。"""
        self._finish_typing_state()

    def _finish_typing_state(self):
        """结束 Bongo 敲键盘状态。"""
        self._release_bongo_tap()
        self.left_hand_tap_timer.stop()
        self.left_hand_tap_phase = 0
        self.left_hand_down = False
        self.active_keys.clear()
        self.held_keys.clear()
        self.key_release_tokens.clear()
        if self.state_machine.get_current_state() == PetState.TYPING:
            self.state_machine.release_state(PetState.TYPING)

    def _on_keyboard_monitor_failed(self, reason):
        """键盘监听失败时给用户一个可见状态。"""
        self.keyboard_status = reason or "键盘监听启动失败"
        self.keyboard_available = False
        if hasattr(self, "tray_icon"):
            self._show_status_popup("桌宠键盘监听未启动", self.keyboard_status, 4500)

    def _on_keyboard_monitor_started(self, status):
        """键盘监听成功启动。"""
        self.keyboard_available = True
        self.keyboard_status = status or "键盘监听已启动"

    def _release_bongo_tap(self):
        """短按键动画自动弹起。"""
        self.bongo_pressed = False
        self._refresh_hand_down_state()
        self.update()

    def _release_left_hand_tap(self):
        """左手敲击层稍晚弹起，让肉眼能看到动作。"""
        self.left_hand_tap_phase = 0
        self._refresh_hand_down_state()
        self.update()

    def _key_to_keyboard_key(self, key):
        """把真实键盘事件转换成键盘 UI 上的具体键位。"""
        if key.startswith("kc:"):
            try:
                return MAC_KEYCODE_TO_KEY_ID.get(int(key.split(":", 1)[1]), "")
            except ValueError:
                return ""

        key_lower = key.lower()
        special_keys = {
            "key.space": "SPACE",
            "key.enter": "ENTER",
            "key.return": "ENTER",
            "key.tab": "TAB",
            "key.backspace": "DEL",
            "key.delete": "DEL",
            "key.esc": "ESC",
            "key.shift": "SHIFT",
            "key.shift_l": "SHIFT",
            "key.shift_r": "SHIFT_R",
            "key.ctrl": "CTRL",
            "key.ctrl_l": "CTRL",
            "key.ctrl_r": "CTRL_R",
            "key.alt": "ALT" if IS_WINDOWS else "OPT",
            "key.alt_l": "ALT" if IS_WINDOWS else "OPT",
            "key.alt_r": "ALT_R" if IS_WINDOWS else "OPT_R",
            "key.cmd": "WIN" if IS_WINDOWS else "CMD",
            "key.cmd_l": "WIN" if IS_WINDOWS else "CMD",
            "key.cmd_r": "WIN_R" if IS_WINDOWS else "CMD_R",
            "key.caps_lock": "CAPS",
            "key.left": "LEFT",
            "key.right": "RIGHT",
            "key.up": "UP",
            "key.down": "DOWN",
        }
        if key_lower in special_keys:
            return special_keys[key_lower]
        if len(key) == 1:
            return key.upper()
        return ""

    def _refresh_hand_down_state(self):
        """左手只跟随每次 keydown 的敲击脉冲，不被长按键位粘住。"""
        self.left_hand_down = self.left_hand_tap_phase > 0
    
    def _on_walk_step(self, direction):
        """走路每一步"""
        current_x = self.x()
        new_x = current_x + direction * WALK_SPEED
        direction_changed = False
        
        # 只在当前停靠点附近小范围走动，避免工作时跑太远。
        margin = 10
        left_limit = max(margin, self.home_position.x() - WALK_RANGE)
        right_limit = min(
            self.screen_geometry.width() - self.width() - margin,
            self.home_position.x() + WALK_RANGE,
        )

        if new_x < left_limit:
            new_x = left_limit
            self.state_machine.walk_direction = 1  # 转向
            direction_changed = True
        elif new_x > right_limit:
            new_x = right_limit
            self.state_machine.walk_direction = -1  # 转向
            direction_changed = True
        
        self.move(new_x, self.y())
        if direction_changed:
            self._update_click_mask()
            self.update()
    
    def _get_display_frame(self):
        """获取用于点击区域计算的逻辑尺寸帧。实际绘制会使用高清源图。"""
        if (
            self.state_machine.get_current_state() == PetState.TYPING
            and not self.typing_scene_base.isNull()
        ):
            return self.typing_scene_base.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        frame = self.animation.get_current_frame()
        if frame:
            scaled = frame.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            if (
                self.state_machine.get_current_state() == PetState.WALKING
                and self.state_machine.walk_direction > 0
            ):
                scaled = scaled.transformed(QTransform().scale(-1, 1))
            return scaled
        return None

    def _current_source_frame(self):
        """获取当前状态的高清源图，避免先缩成低像素图再绘制导致发糊。"""
        if (
            self.state_machine.get_current_state() == PetState.TYPING
            and not self.typing_scene_base.isNull()
        ):
            return self.typing_scene_base
        return self.animation.get_current_frame()

    def _target_rect_for_source(self, source):
        """按窗口逻辑尺寸计算源图的绘制区域，保留原始比例。"""
        if source is None or source.isNull():
            return QRectF()

        scale = min(
            self.width() / max(source.width(), 1),
            self.height() / max(source.height(), 1),
        )
        target_width = source.width() * scale
        target_height = source.height() * scale
        return QRectF(
            (self.width() - target_width) / 2,
            (self.height() - target_height) / 2,
            target_width,
            target_height,
        )

    def _draw_source_pixmap(self, painter, source, y_offset=0, flip=False):
        """直接把高清源图绘制到目标区域，交给 Qt 在设备像素层面缩放。"""
        if source is None or source.isNull():
            return

        target = self._target_rect_for_source(source)
        target.translate(0, y_offset)
        source_rect = QRectF(0, 0, source.width(), source.height())

        if flip:
            painter.save()
            painter.translate(target.center().x(), target.center().y())
            painter.scale(-1, 1)
            flipped_target = QRectF(
                -target.width() / 2,
                -target.height() / 2,
                target.width(),
                target.height(),
            )
            painter.drawPixmap(flipped_target, source, source_rect)
            painter.restore()
            return

        painter.drawPixmap(target, source, source_rect)

    def _display_frame_position(self, frame):
        """根据状态计算角色绘制位置；打字时让小人趴在键盘上方。"""
        x = (self.width() - frame.width()) // 2
        if self.state_machine.get_current_state() == PetState.TYPING:
            return x, (self.height() - frame.height()) // 2
        return x, (self.height() - frame.height()) // 2

    def _typing_desk_top(self):
        """打字状态桌面的上沿。"""
        return int(self.height() * 0.48)

    def _on_animation_frame_changed(self):
        # 透明窗口的 mask 必须跟随每一帧动画同步更新。
        # 否则走路时脚/头发摆到上一帧 mask 外，会被 macOS 裁掉，看起来像肢体消失。
        self._update_click_mask()
        self.update()

    def _region_for_pixmap(self, pixmap):
        """把透明 PNG 的不透明区域转换成窗口点击区域。"""
        cache_key = (int(pixmap.cacheKey()), pixmap.width(), pixmap.height())
        if cache_key in self._mask_cache:
            return self._mask_cache[cache_key]

        image = pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
        region = QRegion()
        for y in range(image.height()):
            start_x = -1
            for x in range(image.width()):
                opaque = image.pixelColor(x, y).alpha() >= CLICK_ALPHA_THRESHOLD
                if opaque and start_x < 0:
                    start_x = x
                elif not opaque and start_x >= 0:
                    region = region.united(QRegion(start_x, y, x - start_x, 1))
                    start_x = -1
            if start_x >= 0:
                region = region.united(QRegion(start_x, y, image.width() - start_x, 1))

        self._mask_cache[cache_key] = region
        return region

    def _update_click_mask(self):
        """只让可见角色区域吃鼠标，透明区域不挡下面窗口。"""
        if not MOUSE_INTERACTION_ENABLED:
            self.clearMask()
            self._last_click_mask_signature = None
            return

        frame = self._get_display_frame()
        if not frame:
            self.clearMask()
            self._last_click_mask_signature = None
            return

        state = self.state_machine.get_current_state()
        source = self._current_source_frame()
        source_key = int(source.cacheKey()) if source and not source.isNull() else int(frame.cacheKey())
        direction = 1 if (state == PetState.WALKING and self.state_machine.walk_direction > 0) else -1
        signature = (
            state,
            self.animation.current_frame,
            direction,
            source_key,
            frame.width(),
            frame.height(),
            self.width(),
            self.height(),
        )
        if signature == self._last_click_mask_signature:
            return

        region = self._region_for_pixmap(frame)
        x, y = self._display_frame_position(frame)
        region = region.translated(x, y)
        if state == PetState.TYPING:
            desk_top = self._typing_desk_top()
            region = region.united(QRegion(0, desk_top, self.width(), self.height() - desk_top))
        self.setMask(region)
        self._last_click_mask_signature = signature

    def _event_hits_visible_pet(self, event):
        """确认鼠标是否真的点在可见角色像素上。"""
        if not MOUSE_INTERACTION_ENABLED:
            return False

        frame = self._get_display_frame()
        if not frame:
            return False

        pos = event.position().toPoint()
        if self.state_machine.get_current_state() == PetState.TYPING and pos.y() >= self._typing_desk_top():
            return True

        frame_x, frame_y = self._display_frame_position(frame)
        img_x = pos.x() - frame_x
        img_y = pos.y() - frame_y
        if img_x < 0 or img_y < 0 or img_x >= frame.width() or img_y >= frame.height():
            return False

        image = frame.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
        return image.pixelColor(img_x, img_y).alpha() >= CLICK_ALPHA_THRESHOLD

    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        source = self._current_source_frame()
        flip = (
            self.state_machine.get_current_state() == PetState.WALKING
            and self.state_machine.walk_direction > 0
        )
        self._draw_source_pixmap(painter, source, flip=flip)

        self._draw_bongo_keyboard(painter)

    def _draw_bongo_keyboard(self, painter):
        """绘制 mongocat/BongoCat 风格桌面：小人趴桌边，真实键盘同步高亮。"""
        if self.state_machine.get_current_state() != PetState.TYPING:
            return

        painter.save()

        keyboard = QRectF(self.width() * 0.35, self.height() * 0.62, self.width() * 0.61, self.height() * 0.30)
        keyboard_transform = self._keyboard_transform(keyboard)
        keyboard_outline = self._keyboard_outline(keyboard, keyboard_transform)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 34)))
        painter.drawPolygon(keyboard_outline.translated(2, 3))
        painter.setBrush(QBrush(QColor(249, 250, 252, 248)))
        painter.setPen(QPen(QColor(22, 22, 22, 235), 1.35))
        painter.drawPolygon(keyboard_outline)

        key_rects = self._keyboard_key_rects(keyboard)
        key_font = QFont("PingFang SC")
        key_font.setPointSizeF(3.6)
        key_font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
        painter.setFont(key_font)

        painter.save()
        painter.setTransform(keyboard_transform, True)
        for key_id, key_rect in key_rects.items():
            pressed = key_id in self.active_keys
            y_offset = 1.4 if pressed else 0
            draw_rect = QRectF(
                key_rect.x(),
                key_rect.y() + y_offset,
                key_rect.width(),
                key_rect.height(),
            )

            if pressed:
                fill = QColor(255, 214, 96, 252)
                border = QColor(18, 18, 18, 245)
                text = QColor(18, 18, 18, 255)
            else:
                fill = QColor(255, 255, 255, 248)
                border = QColor(68, 68, 68, 215)
                text = QColor(36, 36, 36, 245)

            painter.setBrush(QBrush(fill))
            painter.setPen(QPen(border, 0.65))
            painter.drawRoundedRect(draw_rect, 1.6, 1.6)

            label = KEY_DISPLAY_LABELS.get(key_id, key_id)
            painter.setPen(QPen(text, 0.55))
            painter.drawText(draw_rect, Qt.AlignmentFlag.AlignCenter, label)
        painter.restore()

        active_key = self.last_keyboard_key if self.last_keyboard_key in key_rects else ""
        if active_key:
            active_center = keyboard_transform.map(key_rects[active_key].center())
            self._draw_active_key_badge(painter, active_key, active_center)
        else:
            active_center = None

        self._draw_typing_hand_overlay(painter)

        painter.restore()

    def _draw_typing_hand_overlay(self, painter):
        """把休息/敲击手都画在键盘上方，避免手被键盘层盖住。"""
        source = self.typing_tap_overlay if self.left_hand_down else self.typing_rest_overlay
        if source.isNull():
            return

        self._draw_source_pixmap(
            painter,
            source,
            y_offset=3 if self.left_hand_tap_phase else 0,
        )

    def _keyboard_transform(self, keyboard):
        """让键盘轻微倾斜，有参考图里的桌面透视感。"""
        center = keyboard.center()
        transform = QTransform()
        transform.translate(center.x(), center.y())
        transform.rotate(5)
        transform.shear(-0.18, 0)
        transform.translate(-center.x(), -center.y())
        return transform

    def _keyboard_outline(self, keyboard, transform):
        """返回变换后的键盘外框四边形。"""
        return transform.map(QPolygonF([
            keyboard.topLeft(),
            keyboard.topRight(),
            keyboard.bottomRight(),
            keyboard.bottomLeft(),
        ]))

    def _keyboard_key_rects(self, keyboard):
        """按真实键盘行布局计算每个键位的位置。"""
        rects = {}
        pad_x = 4.0
        pad_y = 5.0
        gap_x = 1.0
        gap_y = 1.2
        row_h = (keyboard.height() - pad_y * 2 - gap_y * (len(KEYBOARD_ROWS) - 1)) / len(KEYBOARD_ROWS)

        for row_index, row in enumerate(KEYBOARD_ROWS):
            total_weight = sum(weight for _, weight in row)
            unit_w = (keyboard.width() - pad_x * 2 - gap_x * (len(row) - 1)) / total_weight
            x = keyboard.x() + pad_x
            y = keyboard.y() + pad_y + row_index * (row_h + gap_y)

            for key_id, weight in row:
                key_w = unit_w * weight
                rects[key_id] = QRectF(x, y, key_w, row_h)
                x += key_w + gap_x

        return rects

    def _draw_active_key_badge(self, painter, key_id, center):
        """显示当前敲击键位，弥补迷你键盘文字较小的问题。"""
        label = KEY_DISPLAY_LABELS.get(key_id, key_id)
        badge = QRectF(center.x() - 20, center.y() - 24, 40, 13)
        painter.setBrush(QBrush(QColor(255, 244, 184, 242)))
        painter.setPen(QPen(QColor(163, 116, 29, 220), 0.8))
        painter.drawRoundedRect(badge, 6, 6)
        painter.setFont(QFont("PingFang SC", 7, QFont.Weight.Bold))
        painter.setPen(QPen(QColor(76, 53, 15, 255), 0.8))
        painter.drawText(badge, Qt.AlignmentFlag.AlignCenter, label)

    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件"""
        if not self._event_hits_visible_pet(event):
            event.ignore()
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            
            # 拖拽时切到专用拖拽姿态。
            self.state_machine.notify_activity()
            if self.state_machine.get_current_state() != PetState.TYPING:
                self.state_machine.request_state(PetState.DRAGGING, True)
            
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件（拖拽）"""
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.home_position = QPoint(self.x(), self.y())
            if self.state_machine.get_current_state() == PetState.DRAGGING:
                self.state_machine.release_state(PetState.DRAGGING)
            event.accept()
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """双击事件"""
        if not self._event_hits_visible_pet(event):
            event.ignore()
            return

        if event.button() == Qt.MouseButton.LeftButton:
            # 双击触发开心状态
            self.state_machine.request_state(PetState.HAPPY, True)
            event.accept()
    
    def _show_context_menu(self, pos):
        """显示右键菜单"""
        menu = QMenu(self)
        
        # 状态切换
        state_menu = menu.addMenu("切换状态")
        
        idle_action = QAction("待机", self)
        idle_action.triggered.connect(lambda: self.state_machine.request_state(PetState.IDLE, True))
        state_menu.addAction(idle_action)
        
        happy_action = QAction("开心", self)
        happy_action.triggered.connect(lambda: self.state_machine.request_state(PetState.HAPPY, True))
        state_menu.addAction(happy_action)
        
        sleep_action = QAction("睡觉", self)
        sleep_action.triggered.connect(lambda: self.state_machine.request_state(PetState.SLEEPING, True))
        state_menu.addAction(sleep_action)
        
        walk_action = QAction("走路", self)
        walk_action.triggered.connect(lambda: self.state_machine.request_state(PetState.WALKING, True))
        state_menu.addAction(walk_action)

        surprised_action = QAction("惊讶", self)
        surprised_action.triggered.connect(lambda: self.state_machine.request_state(PetState.SURPRISED, True))
        state_menu.addAction(surprised_action)

        wakeup_action = QAction("醒来", self)
        wakeup_action.triggered.connect(lambda: self.state_machine.request_state(PetState.WAKEUP, True))
        state_menu.addAction(wakeup_action)

        selfie_action = QAction("自拍", self)
        selfie_action.triggered.connect(lambda: self.state_machine.request_state(PetState.SELFIE, True))
        state_menu.addAction(selfie_action)
        
        menu.addSeparator()
        
        # 显示/隐藏
        toggle_action = QAction("隐藏到托盘", self)
        toggle_action.triggered.connect(self._toggle_visible)
        menu.addAction(toggle_action)
        
        # 重置位置
        reset_action = QAction("重置位置", self)
        reset_action.triggered.connect(self._reset_position)
        menu.addAction(reset_action)

        if IS_MAC:
            permission_action = QAction("打开输入监控设置", self)
            permission_action.triggered.connect(self._open_input_monitoring_settings)
            menu.addAction(permission_action)

        test_bongo_action = QAction("测试真实键位动画", self)
        test_bongo_action.triggered.connect(self._test_bongo_tap)
        menu.addAction(test_bongo_action)

        keyboard_status_action = QAction("查看键盘监听状态", self)
        keyboard_status_action.triggered.connect(self._show_keyboard_status)
        menu.addAction(keyboard_status_action)
        
        menu.addSeparator()
        
        # 退出
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)
        
        menu.exec(pos)
    
    def _toggle_visible(self):
        """切换显示/隐藏"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
    
    def _reset_position(self):
        """重置位置到右下角"""
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - self.width() - 50, 
                  screen.height() - self.height() - 50)
        self.home_position = QPoint(self.x(), self.y())

    def _open_input_monitoring_settings(self):
        """打开 macOS 输入监控权限页面。Windows 无需此权限。"""
        if IS_MAC:
            QDesktopServices.openUrl(
                QUrl("x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent")
            )

    def _test_bongo_tap(self):
        """手动测试 BongoCat 风格敲键盘动画。"""
        self._show_status_popup(
            "桌宠测试动画",
            "正在连续演示敲键盘动画；这不代表真实键盘监听已收到按键。",
            2600,
        )
        demo_keys = ["kc:0", "kc:4", "kc:1", "kc:38", "kc:2", "kc:40", "kc:13", "kc:37"]
        for i, key in enumerate(demo_keys * 2):
            QTimer.singleShot(i * 150, lambda k=key: self._trigger_bongo_tap(k))
        QTimer.singleShot(len(demo_keys) * 2 * 150 + 350, self._finish_typing_state)

    def _keyboard_status_text(self):
        """生成当前键盘监听状态文本。"""
        last_key_id = self._key_to_keyboard_key(self.last_real_key)
        last_key_label = KEY_DISPLAY_LABELS.get(last_key_id, last_key_id) or self.last_real_key
        status = (
            f"{self.keyboard_status}\n"
            f"真实按键次数: {self.real_key_count}\n"
            f"最后真实键位: {last_key_label}"
        )
        if self.keyboard_monitor and hasattr(self.keyboard_monitor, "last_error"):
            last_error = self.keyboard_monitor.last_error
            if last_error:
                status = f"{last_error}\n真实按键次数: {self.real_key_count}"
        return status

    def _show_keyboard_status(self):
        """显示当前键盘监听状态。"""
        self._show_status_popup(
            "桌宠键盘监听状态",
            self._keyboard_status_text(),
            6000,
        )

    def _show_status_popup(self, title, message, duration_ms=4000):
        """在桌宠旁边显示一个不依赖系统通知的可见状态气泡。"""
        if self.status_popup:
            self.status_popup.close()

        popup = QWidget()
        popup.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.NoDropShadowWindowHint
        )
        popup.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        popup.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        container = QWidget(popup)
        container.setObjectName("statusBubble")
        container.setStyleSheet(
            """
            QWidget#statusBubble {
                background: rgba(255, 255, 255, 238);
                border: 1px solid rgba(80, 104, 145, 180);
                border-radius: 12px;
            }
            QLabel#titleLabel {
                color: #243049;
                font-weight: 700;
                font-size: 13px;
            }
            QLabel#messageLabel {
                color: #33405f;
                font-size: 12px;
                line-height: 1.35;
            }
            """
        )

        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 9, 12, 10)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setObjectName("titleLabel")
        message_label = QLabel(message)
        message_label.setObjectName("messageLabel")
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        layout.addWidget(title_label)
        layout.addWidget(message_label)

        width = 270
        container.setFixedWidth(width)
        container.adjustSize()
        popup.setFixedSize(container.size())
        container.move(0, 0)

        screen = QGuiApplication.primaryScreen().availableGeometry()
        x = self.x() - popup.width() - 12
        if x < screen.left() + 8:
            x = self.x() + self.width() + 12
        y = min(max(self.y(), screen.top() + 8), screen.bottom() - popup.height() - 8)
        popup.move(x, y)

        self.status_popup = popup
        apply_strong_topmost(popup)
        set_ignores_mouse_events(popup, True)
        popup.show()
        QTimer.singleShot(duration_ms, popup.close)

    def _ensure_topmost(self):
        """重新提升窗口层级，保持桌宠始终浮在最前面。"""
        apply_strong_topmost(self)
        set_ignores_mouse_events(self, not MOUSE_INTERACTION_ENABLED)
    
    def _quit(self):
        """退出应用"""
        if self.keyboard_monitor:
            self.keyboard_monitor.stop()
        self.state_machine.stop()
        self.animation.stop()
        self.bongo_release_timer.stop()
        self.left_hand_tap_timer.stop()
        self.typing_idle_timer.stop()
        if self.status_popup:
            self.status_popup.close()
        QApplication.quit()
    
    def closeEvent(self, event):
        """关闭事件（最小化到托盘）"""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "桌宠",
            "已最小化到系统托盘",
            QSystemTrayIcon.MessageIcon.Information,
            1000
        )
