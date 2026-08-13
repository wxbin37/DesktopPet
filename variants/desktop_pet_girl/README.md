# 🎀 女生版综合桌宠 DesktopPetGirl

这是独立于男生版项目的女生版桌宠：融合 **BongoCat** 键盘互动 + **OnePic Desktop Pet** 多状态动画。

本目录是主仓库中的独立角色变体，运行、素材生成和打包流程与根目录默认版本一致；如果要继续制作其他风格角色，也可以复制本目录作为模板。

## ✨ 功能特性

### 🎭 多种状态动画
- **待机 (idle)** - 呼吸效果，偶尔自动切换状态
- **打字 (typing)** - 键盘输入时同步触发，左手按真实敲击节奏拍键盘
- **走路 (walking)** - 在屏幕上左右走动
- **睡觉 (sleeping)** - 长时间无操作后自动进入睡眠，带 Zzz 效果
- **开心 (happy)** - 点击宠物时触发，跳动+爱心效果

### ⌨️ 键盘互动（BongoCat 风格）
- 全局监听键盘输入
- 每次按键都会立即切换到敲击键盘状态
- 打字 UI 使用专门生成的 mongocat 风格趴桌底图：小人趴在桌边，桌面左侧有触控板
- 默认使用女生 `assets/blue_chibi_hd` 高清资源包：粉紫色可爱动漫女性角色，动作帧和打字桌面按当前桌宠窗口预生成 3× 源图，减少 Retina 屏上的边缘发糊
- 右侧只叠加一套真实 QWERTY/mac 键盘覆盖层，收到哪个真实键位就高亮哪个键位
- 按键逻辑参考 BongoCat 的 pressed-key 覆盖思路：底层是静止趴桌图，中层是真实键盘高亮，上层是休息/下压两张左手覆盖层
- 键位高亮和手部动作已分离：按住键时键位可以持续亮起，但左手会按每次 keydown 做“抬起—下压—弹回”的独立节奏，避免看起来粘在键盘上
- 停止打字后自动恢复原状态
- 菜单栏提供“测试真实键位动画”和“查看键盘监听状态”，方便确认是 UI 问题还是 mac 权限问题

### 🖼️ 窗口特性
- 透明无边框窗口
- 始终置顶显示
- 只有角色可见区域响应鼠标，透明空白区域不影响操作网页、输入框或其他软件
- 左键拖拽移动；松手后自动走路只在原地附近小范围活动
- 右键桌宠或菜单栏图标控制状态、权限设置和退出
- 系统托盘运行
- 支持高 DPI 屏幕

### 🎮 交互方式
| 操作 | 效果 |
|------|------|
| 左键拖拽桌宠本体 | 移动宠物位置 |
| 右键桌宠本体/菜单栏图标 | 切换状态、打开输入监控设置、退出 |
| 点击透明空白区域 | 不影响下方窗口 |
| 打字 | 切换到打字状态 |
| 长时间无操作 | 自动睡觉 |

## 🚀 快速开始

### 安装依赖
```bash
pip install PyQt6 Pillow
```

### 运行
```bash
cd desktop_pet_girl
python main.py
```

### macOS 权限设置
键盘监听功能需要输入监控权限：
1. 打开 **系统设置 > 隐私与安全性 > 输入监控**
2. 添加你运行程序的终端/IDE（如 Terminal、iTerm2、VS Code）
3. 重启应用

如果没有授权，键盘互动功能将不可用，但其他功能正常。

## 📁 项目结构

```
desktop_pet_girl/
├── main.py                  # 程序入口
├── config.py                # 配置文件
├── pet_window.py            # 主窗口类
├── animation_manager.py     # 动画管理器
├── state_machine.py         # 状态机
├── keyboard_monitor.py      # 通用键盘监听器 (Windows/Linux)
├── keyboard_monitor_mac.py  # macOS 原生键盘监听器
├── generate_assets.py       # 素材生成脚本
├── requirements.txt         # 依赖
├── README.md                # 说明文档
└── assets/
    ├── blue_chibi/          # 女生原始角色素材
    └── blue_chibi_hd/       # 女生默认高清角色素材
        ├── typing_mongocat_base.png         # 高清打字桌面休息底图
        ├── typing_mongocat_rest_overlay.png # 高清休息手覆盖层
        ├── typing_mongocat_tap_overlay.png  # 高清敲击手覆盖层
        ├── typing_mongocat_tap.png          # 高清敲击参考帧
        ├── idle/            # 待机动画帧
        ├── typing/          # 打字动画帧
        ├── walking/         # 走路动画帧
        ├── sleeping/        # 睡觉动画帧
        └── happy/           # 开心动画帧
```

## 🎨 自定义角色

### 方法一：替换图片
将你的角色图片放入对应状态文件夹，命名为 `frame_000.png`, `frame_001.png`...

### 方法二：从单张图片生成
修改 `generate_assets.py` 中的 `INPUT_IMAGE` 路径，然后运行：
```bash
python generate_assets.py
```

### 动画帧要求
- PNG 格式，支持透明背景
- 建议尺寸：200x200 像素
- 帧数不限，自动循环播放

## ⚙️ 配置说明

在 `config.py` 中可以调整：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| WINDOW_WIDTH | 窗口宽度 | 220 |
| WINDOW_HEIGHT | 窗口高度 | 155 |
| WINDOW_OPACITY | 窗口透明度 | 1.0 |
| FPS | 动画帧率 | 12 |
| WALK_SPEED | 走路速度 | 2 |
| TYPING_TIMEOUT | 打字超时时间(ms) | 900 |
| SLEEP_AFTER_IDLE | 多久后睡觉(ms) | 30000 |

## 🔧 状态优先级

状态切换遵循优先级规则，高优先级状态可以打断低优先级：

1. **typing** (打字) - 最高优先级
2. **happy** (开心)
3. **sleeping** (睡觉)
4. **walking** (走路)
5. **idle** (待机) - 最低优先级

## 📝 开发说明

### 状态机
- 使用状态栈管理临时状态
- 支持优先级打断
- 自动状态转移概率可配置

### 扩展新状态
1. 在 `config.py` 的 `PetState` 类中添加新状态
2. 在 `assets/blue_chibi/` 下添加对应文件夹和动画帧
3. 在 `state_machine.py` 中添加状态逻辑

## 📋 已知问题

- macOS 首次运行需要授权输入监控
- 部分全屏应用可能会遮挡（可在设置中调整层级）
- 目前只支持单角色，多角色切换待开发

## 📄 许可证

MIT License
