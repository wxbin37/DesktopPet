# DesktopPet

一个 macOS 桌面宠物项目：融合了 **OnePic Desktop Pet** 的多状态桌宠思路，以及 **BongoCat / Mongocat** 风格的键盘互动。桌宠会常驻最前端、可拖拽、可自动待机/走路/睡觉，并在你敲键盘时切换为趴在桌边敲键盘的状态。

当前仓库保存的是一个稳定底座，适合继续扩展跑步动作、替换角色风格、制作不同人物版本。

## 当前版本

仓库里包含两个角色版本：

| 位置 | 说明 | App 名称 |
| --- | --- | --- |
| 根目录 | 默认男生版桌宠 | `DesktopPet.app` |
| `variants/desktop_pet_girl/` | 独立女生版桌宠 | `DesktopPetGirl.app` |

两个版本的功能一致，只是角色素材、应用名和 bundle id 不同。之后如果要做猫咪、女仆、像素风、赛博风等新角色，可以复制一个变体目录再替换素材。

## 功能特性

- 透明无边框窗口，始终置顶
- 左键拖拽角色，松手后以当前位置为活动中心
- 透明空白区域不挡鼠标，只有可见角色/桌面区域响应交互
- 待机、走路、睡觉、开心、惊讶、醒来、拖拽、自拍等状态
- BongoCat 风格键盘互动：监听真实按键，实时高亮键盘键位
- 打字时小人趴在桌边，左手按真实敲击节奏下压/弹回
- 走路窗口 mask 会按每帧同步刷新，避免脚、头发被裁切
- 跑步/走路已升级为 8 帧步态循环：接触、回弹、抬脚、换脚，比原来的两张岔腿图来回闪更顺
- 走路位移节奏与动画帧率同步，减少“身体在滑、腿在闪”的感觉
- 走路素材已清理脚底独立残影/倒影组件
- macOS 打包支持，输出 `.app`，可再制作 `.dmg` 分享包

## 快速运行

建议使用 Python 3.9+。

```bash
cd DesktopPet
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

女生版：

```bash
cd DesktopPet/variants/desktop_pet_girl
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

## macOS 权限

键盘监听需要“输入监控”权限：

1. 打开「系统设置 > 隐私与安全性 > 输入监控」
2. 添加你运行程序的终端或打包后的 App
3. 重新启动桌宠

如果没有授权，桌宠本体仍能运行，只是不会自动响应真实键盘输入。

## 打包 App

根目录男生版：

```bash
cd DesktopPet
.venv/bin/python -m PyInstaller --noconfirm --clean DesktopPet.spec
```

输出：

```text
dist/DesktopPet.app
```

女生版：

```bash
cd DesktopPet/variants/desktop_pet_girl
.venv/bin/python -m PyInstaller --noconfirm --clean DesktopPet.spec
```

输出：

```text
dist/DesktopPetGirl.app
```

制作 DMG 分享包示例：

```bash
hdiutil create -volname DesktopPet -srcfolder dist/DesktopPet.app -ov -format UDZO dist/DesktopPet.dmg
```

## 项目结构

```text
DesktopPet/
├── main.py                       # 程序入口
├── config.py                     # 状态、窗口、动画和键盘配置
├── pet_window.py                 # 主窗口、绘制、鼠标、键盘 UI
├── state_machine.py              # 状态机
├── animation_manager.py          # 动画帧加载与播放
├── keyboard_monitor_mac.py       # macOS 全局键盘监听
├── keyboard_monitor.py           # 其他平台键盘监听占位/兼容
├── mac_window_utils.py           # macOS 窗口层级工具
├── build_fullbody_assets.py      # 从 4×3 角色表生成动作帧
├── extract_typing_overlay.py     # 提取打字手部覆盖层
├── enhance_ui_assets.py          # 生成 3× 高清 Retina 素材
├── DesktopPet.spec               # PyInstaller 打包配置
├── art/                          # 角色源图/透明角色表
├── assets/
│   ├── blue_chibi/               # 标准透明动作素材
│   └── blue_chibi_hd/            # 程序默认使用的高清素材
├── docs/
│   ├── CHARACTER_TEMPLATE.md     # 制作新角色素材的模板流程
│   └── DEVELOPMENT.md            # 开发、测试、打包和版本说明
└── variants/
    └── desktop_pet_girl/         # 女生版独立变体
```

## 制作其他风格桌宠

最稳的方式是复制一个变体目录：

```bash
cp -R variants/desktop_pet_girl variants/desktop_pet_new_style
```

然后按下面顺序替换：

1. 修改 `DesktopPet.spec` 里的 App 名称和 bundle id
2. 修改 `main.py` 里的 `app.setApplicationName(...)`
3. 准备新的 `art/fullbody_sprite_sheet_alpha.png`
4. 运行 `build_fullbody_assets.py`
5. 准备或生成新的打字趴桌图和手部覆盖层
6. 运行 `extract_typing_overlay.py`
7. 运行 `enhance_ui_assets.py`
8. 跑 `test_core.py` 和短启动测试
9. 打包 `.app` / `.dmg`

详细模板见：[docs/CHARACTER_TEMPLATE.md](docs/CHARACTER_TEMPLATE.md)。

## 开发文档

- 角色素材模板：[docs/CHARACTER_TEMPLATE.md](docs/CHARACTER_TEMPLATE.md)
- 开发与打包说明：[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)

## 不提交到 Git 的内容

仓库有意不包含：

- `.venv/`
- `build/`
- `dist/`
- `.dmg`
- `__pycache__/`
- 用户原始私人图片

这些内容只应保存在本地。

## License

MIT License
