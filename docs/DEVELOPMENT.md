# 开发、测试与打包说明

这份文档记录 DesktopPet 的开发底子，方便之后继续优化动画、添加新状态或制作新角色变体。

## 一、运行环境

推荐：

- macOS
- Python 3.9+
- PyQt6
- Pillow
- PyInstaller

安装：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install pyinstaller
```

## 二、核心文件职责

| 文件 | 作用 |
| --- | --- |
| `main.py` | 创建 QApplication 和 PetWindow |
| `config.py` | 窗口尺寸、状态、动画速度、键盘参数 |
| `pet_window.py` | 桌宠窗口、绘制、鼠标交互、打字 UI、窗口 mask |
| `state_machine.py` | 状态切换、自动待机、走路、睡觉 |
| `animation_manager.py` | 加载各状态 PNG 帧并按 FPS 播放 |
| `keyboard_monitor_mac.py` | macOS Quartz 全局键盘监听 |
| `build_fullbody_assets.py` | 从 4×3 角色表生成标准动作帧 |
| `extract_typing_overlay.py` | 从趴桌图中提取手部覆盖层 |
| `enhance_ui_assets.py` | 生成高清 Retina 素材 |
| `DesktopPet.spec` | PyInstaller 打包配置 |

## 三、状态系统

状态定义在 `config.py` 的 `PetState`：

```python
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
```

新增状态时需要同步修改：

1. `config.py`：添加状态和优先级
2. `assets/blue_chibi/<state>/`：添加动画帧
3. `state_machine.py`：添加进入/退出逻辑
4. 需要时在 `pet_window.py` 增加特殊绘制或交互

## 四、窗口 mask 说明

桌宠是透明无边框窗口。为了让透明区域不挡鼠标，程序会把当前 PNG 的不透明区域转换成窗口 mask。

关键点：

- 动画每换一帧，mask 也必须同步更新
- 走路左右转向时，mask 也必须更新
- 否则会出现脚、头发、手臂被上一帧窗口形状裁掉的视觉割裂

相关逻辑在：

```text
pet_window.py
```

核心函数：

- `_get_display_frame()`
- `_region_for_pixmap()`
- `_update_click_mask()`
- `_on_animation_frame_changed()`

## 五、键盘互动说明

键盘互动由两部分组成：

1. `keyboard_monitor_mac.py` 监听真实键盘事件
2. `pet_window.py` 根据按键绘制键位高亮和手部敲击

UI 结构：

- 底层：趴桌人物图 `typing_mongocat_base.png`
- 中层：代码绘制真实键盘和高亮键
- 上层：左手 rest/tap overlay

这样可以做到每个真实键位实时同步，而不是简单播放一张固定 GIF。

## 六、测试命令

基础测试：

```bash
.venv/bin/python test_core.py
```

导入测试：

```bash
.venv/bin/python -B -c 'import main, pet_window; print("imports ok")'
```

短启动测试：

```bash
.venv/bin/python main.py --smoke-test-ms=2200
```

打包后短启动：

```bash
dist/DesktopPet.app/Contents/MacOS/DesktopPet --smoke-test-ms=2200
```

女生版把路径换成：

```bash
dist/DesktopPetGirl.app/Contents/MacOS/DesktopPetGirl --smoke-test-ms=2200
```

## 七、打包流程

```bash
.venv/bin/python -m PyInstaller --noconfirm --clean DesktopPet.spec
```

签名验证：

```bash
codesign --verify --deep --strict --verbose=1 dist/DesktopPet.app
```

制作 DMG：

```bash
hdiutil create -volname DesktopPet -srcfolder dist/DesktopPet.app -ov -format UDZO dist/DesktopPet.dmg
```

## 八、Git 规则

建议提交：

- 源码 `.py`
- `requirements.txt`
- `DesktopPet.spec`
- `README.md`
- `docs/`
- `art/fullbody_sprite_sheet_alpha.png`
- `assets/blue_chibi/`
- `assets/blue_chibi_hd/`

不要提交：

- `.venv/`
- `build/`
- `dist/`
- `.dmg`
- `.DS_Store`
- `__pycache__/`
- 私人原始图片

## 九、继续优化跑步动作的方向

当前走路动作已经修复了裁脚和脚底残影，但动作本身仍可继续优化。推荐方向：

- 从 2 个 walk 姿势扩展到 4 个或 6 个基础姿势
- 在 `STATE_FRAMES["walking"]` 中加入接触、下压、经过、抬脚等中间帧
- 给身体增加轻微上下起伏
- 手臂与腿做相反方向摆动
- 转向时保持同一帧镜像，不重新生成另一套人物
- 保持每帧脚底位置稳定，避免人物像在“闪烁跳帧”

如果对新跑步动作不满意，可以回退到提交的稳定版本，然后只重做 `walking` 相关素材和状态帧配置。

