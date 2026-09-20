# DesktopPet 新角色制作与功能修改交接模板

> 用途：把这份文档交给新的 Codex 会话，让它基于现有 DesktopPet 稳定底座制作新角色、修改动作或扩展功能。目标是复用已经验证过的程序结构，不重新造一个不兼容的桌宠。

## 1. 稳定底座

- GitHub 仓库：<https://github.com/wxbin37/DesktopPet>
- 默认分支：`main`
- 男生版：仓库根目录
- 女生版：`variants/desktop_pet_girl/`
- macOS 输出：`.app` 和 `.dmg`
- Windows 输出：免安装单文件 `.exe` 和分享用 `.zip`
- Windows 自动构建：`.github/workflows/build-windows.yml`

当前底座已经具备：

- 透明、无边框、始终置顶的桌宠窗口
- 点击人物可拖拽，松手后只在当前位置附近活动
- 透明区域不挡鼠标；窗口不抢输入焦点
- 待机、走路、睡觉、醒来、开心、惊讶、拖拽、自拍等状态
- BongoCat/Mongocat 风格打字状态
- 监听真实键盘节奏和键位，但不模拟输入、不记录输入内容
- 真实键位高亮，小人左手按输入节奏敲击键盘
- macOS Quartz 键盘监听和 Windows pynput 键盘监听
- macOS 与 Windows 的非激活式强置顶
- 8 帧走路素材、统一缩放、脚底锚点、逐帧窗口 mask
- macOS 和 Windows 打包、测试及发布流程

## 2. 新角色需求表

开始前复制下面内容并填写。没有特别说明的项目保持现有功能不变。

```text
角色项目名称：[中文名]
程序英文名：[仅英文和数字，例如 DesktopPetCat]
角色类型：[男生/女生/动物/机器人/其他]
画风：[可爱动漫/Q版/像素/手绘/其他]
年龄感：[幼态/少年/青年/不适用]
脸型与五官：[描述]
发型或头部特征：[描述]
服装：[描述]
配饰：[描述]
主色：[颜色]
气质：[慵懒/活泼/安静/傲娇/其他]
参考图片：[已在新会话上传/没有]
需要保留参考图哪些特征：[描述]
需要新增的动作：[没有则写“沿用现有动作”]
需要修改的功能：[没有则写“功能完全沿用”]
需要的平台：[macOS/Windows/两者]
是否保留自拍状态：[是/否]
自拍使用的本地原图：[路径或“稍后提供”]
最终 App/EXE 名称：[名称]
```

## 3. 不可破坏的原则

1. 必须使用现有仓库完成，不得另起炉灶重写桌宠框架。
2. 新角色必须建立独立文件夹或独立变体，不能覆盖现有男生版和女生版。
3. 开始修改前先阅读：
   - `README.md`
   - `docs/CHARACTER_TEMPLATE.md`
   - `docs/DEVELOPMENT.md`
   - `docs/WINDOWS.md`
   - 本文档
4. 用户私人原图只保存在本地，不提交 GitHub，不放入公开 Release。
5. 先生成一张透明背景标准全身候选图，暂停等待用户确认；未经确认不得批量生成动作。
6. 人物确认后再制作全套动作；走路预览再次单独暂停确认。
7. 不能用整个人物图片缩放、压扁、左右抖动来假装走路。
8. 不能周期性 `raise()` 窗口抢焦点；置顶必须保持非激活，不能打断中文输入法候选框。
9. 键盘监听只能读取按键事件用于动画，不允许模拟按键、点击页面、保存或上传输入内容。
10. 修改功能时优先修改变体目录；只有确定是所有角色共用的修复，才同步回稳定底座。

## 4. 标准制作流程

### 阶段 A：准备独立项目

1. 检查 Git、Python、PyQt6、Pillow、PyInstaller 环境。
2. 从 GitHub 获取最新 `main`。
3. 复制一个最接近的新角色变体，例如：

   ```text
   variants/desktop_pet_girl → variants/desktop_pet_new_character
   ```

4. 修改新变体中的应用名、打包名和 bundle id。
5. 确认 Git 工作区状态，保留用户已有改动。

### 阶段 B：只做角色候选图并暂停

分析用户参考图：

- 脸型
- 眼睛、眉毛、鼻子、嘴巴
- 发型或头部特征
- 服装和配饰
- 身材比例
- 主色与气质

输出一张候选图，要求：

- 透明背景 PNG
- 单个完整全身角色
- 正面或轻微三分之二视角
- 头顶、左右、脚底都有透明边距
- 角色没有被裁切
- 没有地面、投影、倒影、水印、文字和边框
- 没有多头、多手、多脚、断肢或粘连
- 能作为后续所有动作的一致性基准

输出后必须暂停，明确询问用户是否确认形象。

### 阶段 C：生成动作素材

形象确认后，至少准备这些状态：

| 状态 | 要求 |
| --- | --- |
| `idle` | 自然站立和眨眼，不能僵硬 |
| `walking` | 左右腿交替、手臂反向摆动、身体轻微起伏 |
| `sleeping` | 姿势稳定，可有少量睡眠符号，但不能生成远离人物的碎片 |
| `wakeup` | 自然揉眼或伸展，动作结束后回到待机 |
| `happy` | 克制、自然的开心表情 |
| `surprised` | 自然克制；可用独立“！”加强，不双手高举、不夸张张嘴 |
| `dragging` | 被提起或悬空的合理姿势 |
| `selfie` | 展示照片；若使用私人原图，只能本地保存 |
| `typing` | 小人趴在桌边，左手有休息帧和敲击帧 |

素材结构：

```text
art/fullbody_sprite_sheet_alpha.png       # 4×3，共 12 格
art/walking_sprite_sheet_alpha.png        # 4×2，共 8 帧，强烈推荐
assets/blue_chibi/typing_mongocat_base.png
assets/blue_chibi/typing_mongocat_tap.png
```

`fullbody_sprite_sheet_alpha.png` 布局：

```text
idle_stand | idle_blink | happy    | surprised
walk_a     | walk_b     | typing_a | typing_b
sleeping   | wakeup     | dragging | selfie
```

`walking_sprite_sheet_alpha.png` 布局：

```text
contact A | rebound A | passing A | lift A
contact B | rebound B | passing B | lift B
```

### 阶段 D：素材质量检查

逐张检查并修复：

- 人物是否始终是同一个角色
- 脸、头发、服装、配饰和颜色是否一致
- 是否出现多头、多手、多腿或断肢
- 头顶、手臂、鞋子是否被裁切
- 是否存在白底、半透明脏边或锯齿
- 是否存在脚底阴影、倒影、圆弧、色块或相邻格子漏出的碎片
- 各帧人物缩放比例是否一致
- 各帧脚底锚点是否稳定
- 左右镜像后人物面向是否与移动方向一致
- 走路是否真的有腿部轨迹，而不是图片闪烁或缩放
- 打字 rest/tap 两帧身体位置是否完全一致
- 左手的手掌、袖子、手臂是否连接自然

### 阶段 E：生成程序素材

在新变体目录中运行：

```bash
python build_fullbody_assets.py
python extract_typing_overlay.py
python enhance_ui_assets.py
python test_core.py
```

程序默认读取 `assets/blue_chibi_hd/`。不要只修改低清素材后忘记重新生成高清目录。

### 阶段 F：单独确认走路

生成 8 帧走路 GIF 或等效预览，并暂停等待用户确认。必须检查：

- 左右腿交替清楚
- 后腿确实向后蹬，前腿确实向前迈
- 手臂与腿方向协调
- 人物不会忽大忽小
- 脚底不会漂浮、陷入地面或产生第二个脚影
- 移动方向与人物朝向一致
- 转向只镜像当前帧，不重新换一套不一致人物

未经用户确认，不进入最终打包。

### 阶段 G：接入、运行和测试

必须验证：

- 透明无边框显示正常
- 切换到其他窗口后仍置顶
- 不会抢走输入焦点
- 中文输入法候选不会被打断
- 点到角色能拖拽，透明区域不挡鼠标
- 角色只在拖放后的中心位置附近移动，不跑遍屏幕
- 打字后立即切换到敲键盘状态
- 真实键位正确高亮
- 只有左手按真实节奏下压和弹回；手臂不断开、不透明异常
- 停止打字后自动退出打字状态
- 睡眠、醒来、自拍等状态能够自然出现
- 所有状态窗口 mask 都按帧刷新，不裁脚、不裁头发
- 右键菜单和系统托盘菜单可用
- 能正常退出，不残留进程

### 阶段 H：打包和交付

macOS：

```bash
python -m PyInstaller --noconfirm --clean DesktopPet.spec
codesign --verify --deep --strict --verbose=1 dist/应用名.app
hdiutil create -volname 应用名 -srcfolder dist/应用名.app -ov -format UDZO dist/应用名.dmg
```

Windows：

- 使用 `DesktopPet.Windows.spec`。
- 必须在真实 Windows x64 环境打包。
- 在 macOS 上通过 `.github/workflows/build-windows.yml` 触发 Windows 构建。
- 下载 `.exe`、分享用 `.zip` 和 `SHA256SUMS.txt`。
- 验证 EXE 是 `PE32+ executable (GUI) x86-64`，并核对 SHA-256。

最终向用户明确提供：

- macOS 应打开哪个 `.dmg` 或 `.app`
- Windows 应打开哪个 `.exe`
- 分享给别人应发送哪个 `.dmg` 或 `.zip`
- 文件的绝对路径和 GitHub Release 地址

## 5. 功能修改索引

| 想修改的内容 | 主要文件 |
| --- | --- |
| 窗口尺寸、移动范围、动画速度 | `config.py` |
| 状态出现概率 | `config.py` 中的 `STATE_TRANSITION` |
| 新增或删除状态 | `config.py`、`state_machine.py`、素材目录 |
| 状态持续时间与切换逻辑 | `state_machine.py` |
| 角色绘制、鼠标拖拽、键盘 UI | `pet_window.py` |
| 动画加载与播放帧率 | `animation_manager.py` |
| macOS 键盘监听 | `keyboard_monitor_mac.py` |
| Windows 键盘监听 | `keyboard_monitor.py` |
| macOS/Windows 强置顶 | `mac_window_utils.py` |
| 动作表切帧、清碎片、脚底锚点 | `build_fullbody_assets.py` |
| 打字手部覆盖层 | `extract_typing_overlay.py` |
| 高清素材 | `enhance_ui_assets.py` |
| macOS 打包 | `DesktopPet.spec` |
| Windows 打包 | `DesktopPet.Windows.spec` |

## 6. Git 与隐私规则

应提交：

- 源码和配置
- 文档
- 新角色的公开生成素材
- `.spec` 和构建工作流

不得提交：

- 用户原始私人照片
- 含私人照片的自拍临时素材
- `.venv/`
- `build/`
- `dist/`
- `.dmg`、本地 `.exe`、ZIP 临时包
- `__pycache__/`

提交前执行：

```bash
git status --short
git diff --check
python test_core.py
```

## 7. 最终验收清单

- [ ] 新角色在独立目录中，旧角色没有被覆盖
- [ ] 标准候选图经过用户确认
- [ ] 全部动作人物一致
- [ ] 透明背景和边缘正常
- [ ] 走路 8 帧经过用户确认
- [ ] 没有脚底残影、碎片和裁切
- [ ] 打字左手动画自然并同步真实键盘
- [ ] 桌宠始终置顶但不抢焦点
- [ ] 拖拽和小范围移动正常
- [ ] 状态概率和持续时间合理
- [ ] macOS 实际运行和打包通过
- [ ] Windows Actions 构建和启动测试通过
- [ ] 私人原图没有进入 Git
- [ ] GitHub 文档已同步
- [ ] 用户拿到明确、可双击的最终文件

## 8. 新会话交接结果格式

新会话完成后，要求它用下面格式汇报：

```text
角色名称：
独立项目目录：
Git 分支/提交：
已确认角色图：
已确认走路预览：
macOS 文件：
Windows 文件：
GitHub Release：
测试结果：
仍需用户处理的事项：
```
