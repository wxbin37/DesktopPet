#!/usr/bin/env python3
"""
从单张图片生成各状态动画帧素材
"""
import os
from PIL import Image, ImageDraw, ImageFont
import math

# 配置
INPUT_IMAGE = "/Users/wxbin/Doubao/chats/2026-08-10/new-chat/pet_image.jpg"
OUTPUT_DIR = "/Users/wxbin/Doubao/chats/2026-08-10/new-chat/desktop_pet/assets/default"
FRAME_SIZE = (200, 200)

# 各状态帧数
FRAMES = {
    "idle": 8,
    "typing": 4,
    "walking": 8,
    "sleeping": 10,
    "happy": 6,
}


def remove_background(img):
    """简单的背景去除（白色背景转透明）"""
    img = img.convert("RGBA")
    data = img.getdata()
    
    new_data = []
    for item in data:
        # 白色或接近白色的像素变透明
        if item[0] > 240 and item[1] > 240 and item[2] > 240:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    
    img.putdata(new_data)
    return img


def fit_to_frame(img, size):
    """将图片缩放到适应帧大小，保持比例"""
    img.thumbnail(size, Image.LANCZOS)
    return img


def create_idle_frames(base_img, count):
    """生成待机动画帧 - 轻微呼吸效果"""
    frames = []
    for i in range(count):
        # 呼吸效果：轻微缩放
        scale = 1.0 + 0.03 * math.sin(2 * math.pi * i / count)
        new_size = (int(base_img.width * scale), int(base_img.height * scale))
        scaled = base_img.resize(new_size, Image.LANCZOS)
        
        # 创建透明画布
        frame = Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0))
        
        # 居中放置
        x = (FRAME_SIZE[0] - scaled.width) // 2
        y = (FRAME_SIZE[1] - scaled.height) // 2
        frame.paste(scaled, (x, y), scaled)
        
        frames.append(frame)
    return frames


def create_typing_frames(base_img, count):
    """生成打字动画帧 - 快速上下抖动"""
    frames = []
    for i in range(count):
        # 快速上下抖动
        offset_y = int(5 * math.sin(2 * math.pi * i / count))
        
        frame = Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0))
        x = (FRAME_SIZE[0] - base_img.width) // 2
        y = (FRAME_SIZE[1] - base_img.height) // 2 + offset_y
        frame.paste(base_img, (x, y), base_img)
        
        frames.append(frame)
    return frames


def create_walking_frames(base_img, count):
    """生成走路动画帧 - 左右摇摆+上下起伏"""
    frames = []
    for i in range(count):
        # 左右摇摆
        tilt = 3 * math.sin(2 * math.pi * i / count)
        # 上下起伏
        offset_y = int(3 * abs(math.sin(2 * math.pi * i / count)))
        
        # 旋转
        rotated = base_img.rotate(tilt, Image.BICUBIC, expand=True)
        
        frame = Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0))
        x = (FRAME_SIZE[0] - rotated.width) // 2
        y = (FRAME_SIZE[1] - rotated.height) // 2 - offset_y
        frame.paste(rotated, (x, y), rotated)
        
        frames.append(frame)
    return frames


def create_sleeping_frames(base_img, count):
    """生成睡觉动画帧 - 缓慢呼吸+Zzz文字"""
    frames = []
    for i in range(count):
        # 更慢的呼吸效果
        scale = 1.0 + 0.02 * math.sin(2 * math.pi * i / count)
        new_size = (int(base_img.width * scale), int(base_img.height * scale))
        scaled = base_img.resize(new_size, Image.LANCZOS)
        
        frame = Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0))
        x = (FRAME_SIZE[0] - scaled.width) // 2
        y = (FRAME_SIZE[1] - scaled.height) // 2
        frame.paste(scaled, (x, y), scaled)
        
        # 添加Zzz
        draw = ImageDraw.Draw(frame)
        try:
            font = ImageFont.truetype("/System/Library/Fonts/MarkerFelt.ttc", 20)
        except:
            font = ImageFont.load_default()
        
        # Zzz位置随帧变化
        z_offset = int(10 * i / count)
        z_x = x + scaled.width - 20 + z_offset
        z_y = y - 10 - z_offset
        
        # 渐隐的Z
        alpha = int(255 * (1 - i / count))
        draw.text((z_x, z_y), "Z", fill=(100, 100, 200, alpha), font=font)
        draw.text((z_x + 15, z_y - 10), "z", fill=(100, 100, 200, int(alpha * 0.7)), font=font)
        draw.text((z_x + 25, z_y - 20), "z", fill=(100, 100, 200, int(alpha * 0.4)), font=font)
        
        frames.append(frame)
    return frames


def create_happy_frames(base_img, count):
    """生成开心动画帧 - 跳动"""
    frames = []
    for i in range(count):
        # 跳动效果
        jump = int(15 * abs(math.sin(2 * math.pi * i / count)))
        
        # 轻微放大
        scale = 1.0 + 0.05 * abs(math.sin(2 * math.pi * i / count))
        new_size = (int(base_img.width * scale), int(base_img.height * scale))
        scaled = base_img.resize(new_size, Image.LANCZOS)
        
        frame = Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0))
        x = (FRAME_SIZE[0] - scaled.width) // 2
        y = (FRAME_SIZE[1] - scaled.height) // 2 + jump
        frame.paste(scaled, (x, y), scaled)
        
        # 添加爱心
        if i % 2 == 0:
            draw = ImageDraw.Draw(frame)
            heart_x = x + scaled.width - 30
            heart_y = y - 10
            draw.text((heart_x, heart_y), "♥", fill=(255, 100, 150, 255))
        
        frames.append(frame)
    return frames


def save_frames(frames, state_name):
    """保存帧到指定目录"""
    state_dir = os.path.join(OUTPUT_DIR, state_name)
    os.makedirs(state_dir, exist_ok=True)
    
    for i, frame in enumerate(frames):
        filename = f"frame_{i:03d}.png"
        filepath = os.path.join(state_dir, filename)
        frame.save(filepath, "PNG")
        print(f"  保存: {filepath}")


def main():
    print("加载基础图片...")
    img = Image.open(INPUT_IMAGE)
    
    print("去除背景...")
    img = remove_background(img)
    
    print("调整大小...")
    img = fit_to_frame(img, (180, 180))  # 留一点边距
    
    print("生成各状态动画帧...")
    
    print("\n[1/5] 生成待机(idle)帧...")
    idle_frames = create_idle_frames(img, FRAMES["idle"])
    save_frames(idle_frames, "idle")
    
    print("\n[2/5] 生成打字(typing)帧...")
    typing_frames = create_typing_frames(img, FRAMES["typing"])
    save_frames(typing_frames, "typing")
    
    print("\n[3/5] 生成走路(walking)帧...")
    walking_frames = create_walking_frames(img, FRAMES["walking"])
    save_frames(walking_frames, "walking")
    
    print("\n[4/5] 生成睡觉(sleeping)帧...")
    sleeping_frames = create_sleeping_frames(img, FRAMES["sleeping"])
    save_frames(sleeping_frames, "sleeping")
    
    print("\n[5/5] 生成开心(happy)帧...")
    happy_frames = create_happy_frames(img, FRAMES["happy"])
    save_frames(happy_frames, "happy")
    
    print("\n✅ 所有素材生成完成！")
    print(f"输出目录: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
