# 噜噜桌宠 · DesktopPetLulu 1.1.2

基于本仓库原有 DesktopPet 框架的独立角色，保留圆润黄色身体、橙色嘴部和头顶小橘子。原男生版和女生版不受影响。

## 直接打开

- macOS（Apple 芯片）：打开 `DesktopPetLulu-macOS-arm64.dmg`，将 `DesktopPetLulu.app` 拖入“应用程序”，再双击应用。
- Windows 10/11 64 位：双击 `DesktopPetLulu-Windows-x64.exe`。也可解压 ZIP，双击其中的 `DesktopPetLulu.exe`。
- 分享给朋友：macOS 发送 DMG；Windows 发送 ZIP。无需安装 Python。
- 当前使用本地临时签名，未进行 Apple 公证或 Windows 商业签名。系统首次运行可能显示来源提示。

## 1.1.2 动作调整

- 新增“戴帽出游”：噜噜戴浅色渔夫帽、斜挎小包，扶帽檐、歪头张望、挥手、眨眼共四张独立姿势。
- 移除旧版“图3·单杠锻炼”。它不再出现在“切换状态”、随机待机动作或安装包中。
- 其余动作、走路动画、置顶、拖拽和打字互动保持原样。

## 1.1.1 动作修订

- 新动作直接列在右键及菜单栏/托盘的“切换状态”里，不再出现额外的“参考图动作”子菜单。
- “软软趴趴”重新绘制为参考图里的低矮软团：身体向后连成一体，小手小脚藏在身侧，表情与趴伏过程更自然。
- “抬头张望”重新绘制眼神、歪头与小手变化；双脚位置保持稳定。

## 1.1.0 参考图动作扩展（当前已移除图3）

根据用户上传的参考图片，当前保留五组原有独立动画，每组四张分别绘制的姿势：

| 参考图 | 新动作 | 动画内容 |
| --- | --- | --- |
| 1 | 搓手卖萌 | 双手合拢、叠手、搓手与闭眼 |
| 2 | 张嘴大笑 | 嘴巴张合、露出一颗小门牙、张臂大笑 |
| 4 | 软软趴趴 | 软团趴伏、低头、侧眼张望、眨眼 |
| 5 | 抬头张望 | 抬眼、歪头、轻碰脸颊、害羞眨眼 |
| 6 | 歪头吐舌 | 歪头、伸舌、卷舌闭眼、收回 |

闲置时会随机出现；右键噜噜或点击菜单栏/托盘图标，进入“切换状态”即可点播。动作播放完毕回到待机，开始打字或拖拽会立即打断。原有走路、睡觉、开心等动作继续保留。

公开源素材为生成的 `art/reference_actions/*_sheet.png`，提示词保存在同目录的 `PROMPTS.json`、`REFINEMENT_1_1_1.md` 和 `HAT_OUTING_PROMPT.md`。用户上传的原图不包含在仓库或安装包内。

## 1.0.1 走路修复

- 一次行走保持同一方向，到活动边界停下休息，下次行走再选择方向。
- 修复屏幕边缘和外接显示器上左右连续跳动，支持负坐标屏幕。
- 保留已确认的 8 帧腿部动作，校正头部横向对齐，避免手脚伸出时整个人物偏移。
- 更新前请先从旧版桌宠菜单选择“退出”，再打开新版；避免同时运行两只噜噜。

## 使用方式

- 左键拖动角色，放下后只在附近活动。
- 双击角色显示开心动作。
- 右键角色或菜单栏/系统托盘图标可以切换状态、重置位置、测试键位动画或退出。
- 输入时左手按键，键盘同步高亮实际键位；停止输入后退出打字状态。
- macOS 首次使用真实键盘互动时，请在“系统设置 → 隐私与安全性 → 输入监控”中允许 DesktopPetLulu，随后退出并重新打开。也可从桌宠菜单打开输入监控设置。
- 自拍状态默认关闭。安装包不包含用户私人照片。

## 隐私与素材

键盘事件仅在内存中用于动画，不模拟键盘/鼠标、不保存或上传输入内容。公开素材均为生成的角色图；用户原始参考图不放入仓库或 Release。

角色轮廓和 8 帧走路已分别经过用户确认。走路使用独立 `art/walking_sprite_sheet_alpha.png`，同一缩放比例、脚底锚点和头部横向对齐；向左移动时只镜像当前帧。待机、眨眼、睡觉、醒来、开心、惊讶、拖拽和打字素材位于本变体内。

## 重建和测试

沿用现有项目的 Python / PyQt6 / Pillow / PyInstaller 流程：

```sh
python prepare_lulu_assets.py
python build_fullbody_assets.py
python build_reference_actions.py
python extract_typing_overlay.py
python enhance_ui_assets.py
python test_core.py
QT_QPA_PLATFORM=offscreen python test_lulu.py
python main.py --smoke-test-ms=2200
python -m PyInstaller --noconfirm --clean DesktopPet.spec
```

Windows 构建使用 `DesktopPet.Windows.spec`，工作流为 `.github/workflows/build-lulu.yml`。自动检查真实 Windows x64 下的键盘监听导入、交互逻辑、PNG、打包后短启动，并产生 EXE、ZIP 和校验文件。无界面自动测试不会向操作系统注入按键。

macOS 产物为 Apple Silicon arm64。输入监控授权、其他应用焦点和中文输入法候选框需在有桌面及用户授权的环境中核验；自动测试不等同于跨平台实机人工验收。
