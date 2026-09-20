"""
状态机 - 管理桌宠的状态切换逻辑
"""
import random
import time
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from config import (
    PetState, STATE_PRIORITY, STATE_TRANSITION,
    IDLE_INTERVAL, WALK_INTERVAL, WALK_STEP_INTERVAL, SLEEP_AFTER_IDLE, SELFIE_ENABLED
)


class StateMachine(QObject):
    # 状态改变信号
    state_changed = pyqtSignal(str)
    # 请求移动信号（走路状态）
    walk_requested = pyqtSignal(int)  # direction: -1左, 1右

    def __init__(self):
        super().__init__()
        self.current_state = PetState.IDLE
        self.target_state = None
        self.state_stack = []  # 状态栈，用于临时状态恢复

        # 计时器
        self.idle_timer = QTimer()
        self.idle_timer.timeout.connect(self._on_idle_timeout)

        self.walk_timer = QTimer()
        self.walk_timer.setSingleShot(True)
        self.walk_timer.timeout.connect(self._on_walk_timeout)

        self.sleep_timer = QTimer()
        self.sleep_timer.setSingleShot(True)
        self.sleep_timer.timeout.connect(self._on_sleep_timeout)

        # 走路方向
        self.walk_direction = 1
        self.walk_step_timer = QTimer()
        self.walk_step_timer.timeout.connect(self._on_walk_step)

        # 最后活动时间
        self.last_activity_time = time.time() * 1000

    def start(self):
        """启动状态机"""
        self.idle_timer.start(IDLE_INTERVAL)
        self.sleep_timer.start(SLEEP_AFTER_IDLE)

    def stop(self):
        """停止状态机"""
        self.idle_timer.stop()
        self.walk_timer.stop()
        self.sleep_timer.stop()
        self.walk_step_timer.stop()

    def request_state(self, state, priority_override=False):
        """
        请求切换状态
        priority_override: 是否忽略优先级强制切换
        """
        if state == PetState.SELFIE and not SELFIE_ENABLED:
            return False
        if state == self.current_state:
            return False

        # 优先级检查
        if not priority_override and state in STATE_PRIORITY:
            current_priority = STATE_PRIORITY.get(self.current_state, 0)
            new_priority = STATE_PRIORITY.get(state, 0)
            if new_priority < current_priority:
                # 低优先级不能打断高优先级状态
                return False

        # 保存当前状态到栈（用于临时状态恢复）
        if state in [
            PetState.TYPING,
            PetState.HAPPY,
            PetState.SURPRISED,
            PetState.WAKEUP,
            PetState.SELFIE,
            PetState.DRAGGING,
        ]:
            restore = PetState.IDLE if state == PetState.WAKEUP and self.current_state == PetState.SLEEPING else self.current_state
            self.state_stack.append(restore)

        self._change_state(state)
        return True

    def release_state(self, state):
        """
        释放一个临时状态，恢复到之前的状态
        """
        if self.current_state != state:
            return False

        if self.state_stack:
            prev_state = self.state_stack.pop()
            self._change_state(prev_state)
        else:
            self._change_state(PetState.IDLE)
        return True

    def _change_state(self, new_state):
        """执行状态切换"""
        old_state = self.current_state
        self.current_state = new_state

        # 重置活动时间
        self.last_activity_time = time.time() * 1000

        # 状态进入处理
        self._on_state_enter(new_state, old_state)

        # 发出信号
        self.state_changed.emit(new_state)

    def _on_state_enter(self, new_state, old_state):
        """进入新状态时的处理"""
        # 停止所有特定状态的计时器
        self.walk_timer.stop()
        self.walk_step_timer.stop()

        if new_state == PetState.IDLE:
            self.idle_timer.start(IDLE_INTERVAL)
            self.sleep_timer.start(SLEEP_AFTER_IDLE)

        elif new_state == PetState.WALKING:
            # 随机走路时长
            duration = random.randint(2000, 5000)
            self.walk_timer.start(duration)
            self.walk_step_timer.start(WALK_STEP_INTERVAL)
            # 随机方向
            self.walk_direction = random.choice([-1, 1])

        elif new_state == PetState.SLEEPING:
            self.idle_timer.stop()
            self.sleep_timer.stop()

        elif new_state == PetState.TYPING:
            self.idle_timer.stop()
            self.sleep_timer.stop()

        elif new_state == PetState.HAPPY:
            # 开心状态持续一段时间后自动恢复
            QTimer.singleShot(2000, self._on_happy_timeout)

        elif new_state == PetState.SURPRISED:
            QTimer.singleShot(1800, lambda: self._release_if_current(PetState.SURPRISED))

        elif new_state == PetState.WAKEUP:
            QTimer.singleShot(1800, lambda: self._release_if_current(PetState.WAKEUP))

        elif new_state == PetState.SELFIE:
            QTimer.singleShot(2600, lambda: self._release_if_current(PetState.SELFIE))

    def _on_idle_timeout(self):
        """待机超时，随机切换状态"""
        if self.current_state != PetState.IDLE:
            return

        # 根据转移概率选择下一个状态
        transitions = STATE_TRANSITION.get(PetState.IDLE, {PetState.IDLE: 1.0})
        states = list(transitions.keys())
        probabilities = list(transitions.values())

        next_state = random.choices(states, weights=probabilities, k=1)[0]

        if next_state != PetState.IDLE:
            self.request_state(next_state, priority_override=True)

    def _on_walk_timeout(self):
        """走路结束，回到待机"""
        if self.current_state == PetState.WALKING:
            self._change_state(PetState.IDLE)

    def _on_walk_step(self):
        """走路每一步"""
        if self.current_state == PetState.WALKING:
            self.walk_requested.emit(self.walk_direction)

    def _on_sleep_timeout(self):
        """长时间无操作，进入睡眠"""
        if self.current_state == PetState.IDLE:
            self._change_state(PetState.SLEEPING)

    def _on_happy_timeout(self):
        """开心状态结束"""
        self._release_if_current(PetState.HAPPY)

    def _release_if_current(self, state):
        """如果仍停留在指定状态，则恢复上一个状态。"""
        if self.current_state == state:
            self.release_state(state)

    def notify_activity(self):
        """通知有活动（重置睡眠计时器）"""
        if self.current_state == PetState.SLEEPING:
            self.request_state(PetState.WAKEUP, priority_override=True)
        elif self.current_state == PetState.IDLE:
            self.sleep_timer.start(SLEEP_AFTER_IDLE)

    def get_current_state(self):
        """获取当前状态"""
        return self.current_state
