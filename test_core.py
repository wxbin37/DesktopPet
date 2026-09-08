#!/usr/bin/env python3
"""
核心功能测试脚本（不启动GUI）
"""
import sys
import os
import platform
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import ASSETS_DIR, DEFAULT_CHARACTER, PET_STATES, PetState, STATE_PRIORITY, STATE_TRANSITION


def test_config():
    """测试配置"""
    print("=== 配置测试 ===")
    print(f"状态列表: {[v for k, v in vars(PetState).items() if not k.startswith('_')]}")
    print(f"状态优先级: {STATE_PRIORITY}")
    print(f"状态转移: {STATE_TRANSITION}")
    print("✅ 配置测试通过\n")


def test_animation_frames():
    """测试动画帧文件"""
    print("=== 动画帧测试 ===")
    assets_dir = os.path.join(ASSETS_DIR, DEFAULT_CHARACTER)
    
    states = PET_STATES
    all_ok = True
    
    for state in states:
        state_dir = os.path.join(assets_dir, state)
        if os.path.exists(state_dir):
            files = [f for f in os.listdir(state_dir) if f.endswith('.png')]
            print(f"  {state}: {len(files)} 帧")
            if len(files) == 0:
                print(f"    ⚠️  警告: {state} 状态没有动画帧")
                all_ok = False
        else:
            print(f"  {state}: ❌ 目录不存在")
            all_ok = False
    
    if all_ok:
        print("✅ 动画帧测试通过\n")
    else:
        print("⚠️  动画帧测试有警告\n")


def test_state_machine_logic():
    """测试状态机逻辑（不启动Qt事件循环）"""
    print("=== 状态机逻辑测试 ===")
    
    # 测试优先级
    print("状态优先级排序（从低到高）:")
    sorted_states = sorted(STATE_PRIORITY.items(), key=lambda x: x[1])
    for state, priority in sorted_states:
        print(f"  {state}: {priority}")
    
    # 测试打字状态优先级最高
    typing_priority = STATE_PRIORITY.get(PetState.TYPING, 0)
    idle_priority = STATE_PRIORITY.get(PetState.IDLE, 0)
    if typing_priority > idle_priority:
        print("\n✅ 打字状态优先级高于待机状态（正确）")
    else:
        print("\n❌ 状态优先级错误")
    
    print()


def test_windows_keyboard_layout():
    """Windows 构建时检查真实键位映射和 Windows 键帽。"""
    if platform.system() != "Windows":
        return

    from pet_window import KEYBOARD_ROWS, PetWindow

    key_ids = {key_id for row in KEYBOARD_ROWS for key_id, _ in row}
    assert "WIN" in key_ids
    assert "ALT" in key_ids
    assert PetWindow._key_to_keyboard_key(None, "key.cmd") == "WIN"
    assert PetWindow._key_to_keyboard_key(None, "key.alt") == "ALT"
    assert PetWindow._key_to_keyboard_key(None, "key.ctrl_l") == "CTRL"
    print("✅ Windows 键盘映射测试通过\n")


def main():
    print("桌宠核心功能测试\n")
    
    test_config()
    test_animation_frames()
    test_state_machine_logic()
    test_windows_keyboard_layout()
    
    print("=" * 30)
    print("测试完成！")
    print("\n启动桌宠请运行: python main.py")
    print("macOS 用户请确保已授权输入监控权限")


if __name__ == "__main__":
    main()
