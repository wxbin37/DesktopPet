# 角色素材模板与制作流程

这份文档用于把同一个桌宠程序换成其他风格角色。目标是让新角色保持一致性，不出现不同动作像不同人物、走路裁脚、脚底残影、打字手部不跟随等问题。

## 一、素材总览

程序默认读取：

```text
assets/blue_chibi_hd/
```

`blue_chibi_hd` 是由 `assets/blue_chibi` 生成的高清版。通常不要手动改 `blue_chibi_hd`，而是改源图或标准素材后重新运行生成脚本。

核心素材分三类：

| 类型 | 位置 | 说明 |
| --- | --- | --- |
| 4×3 角色源表 | `art/fullbody_sprite_sheet_alpha.png` | 用于生成站立、走路、睡觉等动作 |
| 标准动作帧 | `assets/blue_chibi/<state>/frame_000.png` | 透明 PNG，程序可直接读取 |
| 高清动作帧 | `assets/blue_chibi_hd/<state>/frame_000.png` | Retina 友好，默认运行使用 |
| 打字桌面底图 | `assets/blue_chibi/typing_mongocat_base.png` | 趴桌静止图 |
| 打字下压图 | `assets/blue_chibi/typing_mongocat_tap.png` | 手按键盘时的参考图 |
| 手部覆盖层 | `typing_mongocat_*_overlay.png` | 覆盖在键盘上方，形成敲击效果 |

## 二、4×3 角色源表

`build_fullbody_assets.py` 期望一张 4 列 × 3 行的透明 PNG：

```text
┌────────────┬────────────┬────────────┬────────────┐
│ idle_stand │ idle_blink │ happy      │ surprised  │
├────────────┼────────────┼────────────┼────────────┤
│ walk_a     │ walk_b     │ typing_a   │ typing_b   │
├────────────┼────────────┼────────────┼────────────┤
│ sleeping   │ wakeup     │ dragging   │ selfie     │
└────────────┴────────────┴────────────┴────────────┘
```

文件路径：

```text
art/fullbody_sprite_sheet_alpha.png
```

要求：

- PNG 透明背景
- 角色尽量居中
- 每个格子里人物比例一致
- 头顶、脚底、左右都留一点透明边距
- 不要带地面阴影、反光、投影、水印、边框
- 每格只出现一个完整人物，不要多头、多手、多腿

如果用 AI 生成角色表，建议提示词强调：

- same character consistency
- transparent background
- chibi full body
- 4 columns by 3 rows sprite sheet
- no floor shadow
- no reflection
- no extra limbs
- no cropped head or feet

## 三、动作生成

替换 `art/fullbody_sprite_sheet_alpha.png` 后运行：

```bash
python build_fullbody_assets.py
```

脚本会生成：

```text
assets/blue_chibi/idle/
assets/blue_chibi/walking/
assets/blue_chibi/typing/
assets/blue_chibi/sleeping/
assets/blue_chibi/happy/
assets/blue_chibi/surprised/
assets/blue_chibi/wakeup/
assets/blue_chibi/dragging/
assets/blue_chibi/selfie/
```

脚本里已经包含一个保护：走路帧会清理“人物主体下方断开的地面阴影/倒影组件”。这可以避免桌宠跑动时脚底出现一条不真实的残影。

## 四、走路动作注意事项

当前基础版会用 `walk_a` 和 `walk_b` 两个源姿势生成 8 帧步态循环：接触、回弹、抬脚、换脚，然后进入另一只脚的同样阶段。脚本会加入轻微倾斜、压缩/伸展和上下起伏，避免只有两张岔腿图来回闪。

好看的走路素材应该满足：

- 双脚有清晰交替
- 一帧左脚前，另一帧右脚前
- 身体重心略有起伏
- 手臂最好和腿相反方向摆动
- 每一帧人物高度不要差太大
- 脚不要贴画布底边
- 不要让鞋子和腿被衣服完全遮住

如果要继续优化跑步动作，推荐提供更多源姿势（例如 `walk_contact`、`walk_down`、`walk_pass`、`walk_up`），再在 `build_fullbody_assets.py` 的 `STATE_FRAMES["walking"]` 中加入更多真实中间帧。只有 `walk_a/walk_b` 两张源图时，脚本会尽量通过变形缓和过渡，但无法做到真正逐关节动画。

## 五、打字桌面 UI 素材

打字 UI 类似 BongoCat / Mongocat：

- 小人趴在桌边
- 桌面右侧是程序绘制的真实键盘
- 键位高亮由代码实时绘制
- 手部覆盖层负责显示敲击动作

源素材：

```text
assets/blue_chibi/typing_mongocat_base.png
assets/blue_chibi/typing_mongocat_tap.png
```

然后运行：

```bash
python extract_typing_overlay.py
```

生成：

```text
assets/blue_chibi/typing_mongocat_rest_overlay.png
assets/blue_chibi/typing_mongocat_tap_overlay.png
```

注意：

- 不要把键盘画死在人物图里，键盘由代码绘制
- 桌面左侧可以有触控板
- 小人的手应该在键盘区域上方
- 下压图只需要左手变化，右手可以不动
- rest/tap 两张图的人物位置要严格一致

## 六、生成高清资源

标准素材生成后运行：

```bash
python enhance_ui_assets.py
```

生成：

```text
assets/blue_chibi_hd/
```

程序默认使用 `blue_chibi_hd`，因为它更适合 Retina 屏幕。

## 七、新建角色变体建议流程

复制一个已有变体：

```bash
cp -R variants/desktop_pet_girl variants/desktop_pet_new_style
```

在新目录中：

1. 修改 `DesktopPet.spec`
   - `name`
   - `BUNDLE name`
   - `bundle_identifier`
   - `CFBundleName`
   - `CFBundleDisplayName`
2. 修改 `main.py`
   - `app.setApplicationName(...)`
3. 替换 `art/fullbody_sprite_sheet_alpha.png`
4. 生成标准动作帧：
   ```bash
   python build_fullbody_assets.py
   ```
5. 替换打字趴桌图：
   ```text
   assets/blue_chibi/typing_mongocat_base.png
   assets/blue_chibi/typing_mongocat_tap.png
   ```
6. 提取手部覆盖层：
   ```bash
   python extract_typing_overlay.py
   ```
7. 生成高清素材：
   ```bash
   python enhance_ui_assets.py
   ```
8. 测试：
   ```bash
   python test_core.py
   python main.py
   ```
9. 打包：
   ```bash
   python -m PyInstaller --noconfirm --clean DesktopPet.spec
   ```

## 八、发布前检查清单

发布前至少检查：

- 每个状态目录都有 `frame_000.png` 起步的 PNG
- 透明背景正常，没有白底/绿底
- 走路时没有脚底残影
- 左右转向不会裁脚
- 透明区域不挡鼠标
- 打字时真实键位能高亮
- 手部下压和弹回节奏自然
- `dist/`、`.dmg`、`.venv/` 不提交到 Git
