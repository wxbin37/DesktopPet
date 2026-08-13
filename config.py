"""
桌宠配置文件
"""
import os
import sys

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def resource_path(*parts):
    """Return a path that works both from source and from a PyInstaller app."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_dir = sys._MEIPASS
    else:
        base_dir = BASE_DIR
    return os.path.join(base_dir, *parts)

# 素材目录
ASSETS_DIR = resource_path("assets")
DEFAULT_CHARACTER = "blue_chibi_hd"

# 窗口设置
WINDOW_WIDTH = 220
WINDOW_HEIGHT = 155
WINDOW_OPACITY = 1.0
ALWAYS_ON_TOP = True
CLICK_ALPHA_THRESHOLD = 24
MOUSE_INTERACTION_ENABLED = True

# 动画设置
FPS = 12  # 帧率
IDLE_INTERVAL = 3000  # 待机状态切换间隔(ms)
WALK_SPEED = 2  # 走路速度(像素/帧)
WALK_RANGE = 48  # 自动走路时离当前位置的最大距离(像素)
WALK_INTERVAL = 5000  # 走路触发间隔(ms)
WALK_STEP_INTERVAL = int(1000 / FPS)  # 走路位移和动画帧同步，避免腿在闪、身体在滑
SLEEP_AFTER_IDLE = 30000  # 多久无操作后睡觉(ms)

# 键盘互动
TYPING_TIMEOUT = 900  # 停止打字后多久退出打字状态(ms)
TYPING_COOLDOWN = 100  # 打字状态刷新间隔(ms)
BONGO_TAP_RELEASE_MS = 120  # BongoCat 风格按键弹起延迟(ms)
BONGO_KEY_HOLD_MS = 180  # 键位高亮的兜底保持时间(ms)

# 状态定义
class PetState:
    IDLE = "idle"
    TYPING = "typing"
    WALKING = "walking"
    SLEEPING = "sleeping"
    HAPPY = "happy"
    SURPRISED = "surprised"
    WAKEUP = "wakeup"
    DRAGGING = "dragging"
    SELFIE = "selfie"


PET_STATES = [
    PetState.IDLE,
    PetState.TYPING,
    PetState.WALKING,
    PetState.SLEEPING,
    PetState.HAPPY,
    PetState.SURPRISED,
    PetState.WAKEUP,
    PetState.DRAGGING,
    PetState.SELFIE,
]

# 状态优先级（数值越大优先级越高）
STATE_PRIORITY = {
    PetState.IDLE: 0,
    PetState.WALKING: 1,
    PetState.SLEEPING: 2,
    PetState.HAPPY: 3,
    PetState.SURPRISED: 3,
    PetState.WAKEUP: 3,
    PetState.SELFIE: 3,
    PetState.DRAGGING: 4,
    PetState.TYPING: 4,
}

# 状态切换概率
STATE_TRANSITION = {
    PetState.IDLE: {
        PetState.WALKING: 0.3,
        PetState.HAPPY: 0.1,
        PetState.IDLE: 0.6,
    },
    PetState.WALKING: {
        PetState.IDLE: 0.5,
        PetState.HAPPY: 0.2,
        PetState.WALKING: 0.3,
    },
}
