"""
动画管理器 - 负责加载和管理各状态的动画帧
"""
import os
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QTimer
from config import ASSETS_DIR, DEFAULT_CHARACTER, FPS, PET_STATES, PetState


class AnimationManager:
    def __init__(self, character=DEFAULT_CHARACTER):
        self.character = character
        self.character_dir = os.path.join(ASSETS_DIR, character)
        self.animations = {}  # {state: [QPixmap, ...]}
        self.current_state = PetState.IDLE
        self.current_frame = 0
        self.frame_count = 0
        
        # 动画定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self._next_frame)
        self.frame_delay = int(1000 / FPS)
        
        # 回调函数
        self.on_frame_changed = None
        
        self._load_all_animations()
        
        # 设置初始状态的帧数
        if PetState.IDLE in self.animations:
            self.frame_count = len(self.animations[PetState.IDLE])
    
    def _load_all_animations(self):
        """加载所有状态的动画帧"""
        for state in PET_STATES:
            self._load_animation(state)
    
    def _load_animation(self, state):
        """加载指定状态的动画帧"""
        state_dir = os.path.join(self.character_dir, state)
        frames = []
        
        if os.path.exists(state_dir):
            # 按文件名排序加载所有png图片
            files = sorted([f for f in os.listdir(state_dir) if f.endswith('.png')])
            for file in files:
                pixmap = QPixmap(os.path.join(state_dir, file))
                if not pixmap.isNull():
                    frames.append(pixmap)
        
        # 如果没有帧，添加一个空白占位
        if not frames:
            empty = QPixmap(200, 200)
            empty.fill()
            frames.append(empty)
        
        self.animations[state] = frames
    
    def set_state(self, state):
        """切换动画状态"""
        if state == self.current_state:
            return False
        
        if state in self.animations:
            self.current_state = state
            self.current_frame = 0
            self.frame_count = len(self.animations[state])
            return True
        return False
    
    def get_current_frame(self):
        """获取当前帧"""
        if self.current_state in self.animations and self.frame_count > 0:
            idx = self.current_frame % self.frame_count
            return self.animations[self.current_state][idx]
        return None

    def set_frame(self, index):
        """立即跳到当前状态的指定帧。"""
        if self.frame_count <= 0:
            return
        self.current_frame = index % self.frame_count
        if self.on_frame_changed:
            self.on_frame_changed()
    
    def start(self):
        """开始播放动画"""
        self.timer.start(self.frame_delay)
    
    def stop(self):
        """停止播放动画"""
        self.timer.stop()
    
    def _next_frame(self):
        """切换到下一帧"""
        self.current_frame = (self.current_frame + 1) % max(self.frame_count, 1)
        if self.on_frame_changed:
            self.on_frame_changed()
    
    def get_state_duration(self, state):
        """获取某状态动画的总时长(ms)"""
        if state in self.animations:
            return len(self.animations[state]) * self.frame_delay
        return 1000
