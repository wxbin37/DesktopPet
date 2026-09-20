#!/usr/bin/env python3
"""Build transparent full-body desktop pet frames from a 4x3 sprite sheet."""
from pathlib import Path

from PIL import Image


PROJECT_DIR = Path(__file__).resolve().parent
SHEET_PATH = PROJECT_DIR / "art" / "fullbody_sprite_sheet_alpha.png"
WALKING_SHEET_PATH = PROJECT_DIR / "art" / "walking_sprite_sheet_alpha.png"
OUTPUT_DIR = PROJECT_DIR / "assets" / "blue_chibi"
FRAME_SIZE = (320, 320)
GRID = (4, 3)
WALKING_GRID = (4, 2)


POSES = {
    "idle_stand": 0,
    "idle_blink": 1,
    "happy": 2,
    "surprised": 3,
    "walk_a": 4,
    "walk_b": 5,
    "typing_a": 6,
    "typing_b": 7,
    "sleeping": 8,
    "wakeup": 9,
    "dragging": 10,
    "selfie": 11,
}


STATE_FRAMES = {
    "idle": [("idle_stand", 0, 0)] * 16 + [("idle_stand", 0, -1)] * 16 + [("idle_blink", 0, 0)] * 2 + [("idle_stand", 0, 0)] * 2,
    "walking": [
        # Fallback only. When art/walking_sprite_sheet_alpha.png exists, the
        # script uses that dedicated 4x2 walking cycle instead. Do not fake a
        # gait here by scaling or rotating the whole body; it reads as the
        # image pulsing rather than the legs moving.
        ("walk_a", -1, 2),
        ("walk_a", 0, 0),
        ("walk_b", 1, -1),
        ("walk_b", 1, 0),
        ("walk_b", 1, 2),
        ("walk_b", 0, 0),
        ("walk_a", -1, -1),
        ("walk_a", -1, 0),
    ],
    "typing": [
        ("typing_a", 0, 4),
        ("typing_b", 1, -5),
        ("typing_a", -1, 3),
        ("typing_b", 1, -5),
        ("typing_a", 0, 2),
        ("typing_b", -1, -4),
    ],
    "sleeping": [
        ("sleeping", 0, 1),
        ("sleeping", 0, 0),
        ("sleeping", 0, -1),
        ("sleeping", 0, 0),
    ],
    "happy": [
        ("happy", 0, 4),
        ("happy", 0, -6),
        ("happy", 0, -10),
        ("happy", 0, -4),
        ("happy", 0, 2),
        ("idle_stand", 0, 0),
    ],
    "surprised": [
        ("surprised", 0, 0),
        ("surprised", 0, -2),
        ("surprised", 0, 0),
        ("surprised", 0, 1),
    ],
    "wakeup": [
        ("wakeup", 0, 1),
        ("wakeup", 0, -1),
        ("wakeup", 0, -3),
        ("idle_blink", 0, 0),
    ],
    "dragging": [
        ("dragging", 0, 2),
        ("dragging", -2, -1),
        ("dragging", 2, -2),
        ("dragging", 0, 1),
    ],
    "selfie": [
        ("selfie", 0, 0),
        ("selfie", 0, -2),
        ("selfie", 0, -1),
        ("selfie", 0, 0),
    ],
}


def crop_cell(sheet, index, grid=GRID):
    cols, rows = grid
    col = index % cols
    row = index // cols
    left = round(sheet.width * col / cols)
    upper = round(sheet.height * row / rows)
    right = round(sheet.width * (col + 1) / cols)
    lower = round(sheet.height * (row + 1) / rows)
    return sheet.crop((left, upper, right, lower))


def trim_alpha(image):
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        return image
    return image.crop(bbox)


def alpha_components(image, threshold=2):
    """Return connected alpha components for artifact cleanup."""
    alpha = image.getchannel("A")
    width, height = alpha.size
    pixels = alpha.load()
    seen = bytearray(width * height)
    components = []

    for y in range(height):
        for x in range(width):
            index = y * width + x
            if seen[index] or pixels[x, y] <= threshold:
                continue

            stack = [(x, y)]
            seen[index] = 1
            component_pixels = []
            min_x = max_x = x
            min_y = max_y = y

            while stack:
                cx, cy = stack.pop()
                component_pixels.append((cx, cy))
                min_x = min(min_x, cx)
                max_x = max(max_x, cx)
                min_y = min(min_y, cy)
                max_y = max(max_y, cy)

                for ny in range(cy - 1, cy + 2):
                    if ny < 0 or ny >= height:
                        continue
                    for nx in range(cx - 1, cx + 2):
                        if nx == cx and ny == cy:
                            continue
                        if nx < 0 or nx >= width:
                            continue

                        next_index = ny * width + nx
                        if seen[next_index] or pixels[nx, ny] <= threshold:
                            continue
                        seen[next_index] = 1
                        stack.append((nx, ny))

            components.append(
                {
                    "area": len(component_pixels),
                    "bbox": (min_x, min_y, max_x + 1, max_y + 1),
                    "pixels": component_pixels,
                }
            )

    return components


def remove_detached_lower_artifacts(image):
    """Remove detached ground-shadow/reflection fragments below the main body."""
    image = image.convert("RGBA")
    components = alpha_components(image)
    if len(components) < 2:
        return image

    main = max(components, key=lambda component: component["area"])
    main_bottom = main["bbox"][3]
    cleaned = image.copy()
    output_pixels = cleaned.load()
    removed = False

    for component in components:
        if component is main:
            continue
        left, top, right, bottom = component["bbox"]
        if component["area"] < 10:
            continue
        if top < main_bottom + 8:
            continue

        # The unwanted artifacts are detached, low, flat/wide components under
        # the feet. Keeping this rule narrow avoids deleting real shoes/limbs.
        width = right - left
        height = bottom - top
        if width < 18 and height > 10:
            continue

        for x, y in component["pixels"]:
            red, green, blue, _alpha = output_pixels[x, y]
            output_pixels[x, y] = (red, green, blue, 0)
        removed = True

    return cleaned if removed else image


def remove_remote_artifacts(image, margin=8):
    """Remove isolated fragments that leaked in from neighbouring sprite cells."""
    image = image.convert("RGBA")
    components = alpha_components(image)
    if len(components) < 2:
        return image

    main = max(components, key=lambda component: component["area"])
    main_left, main_top, main_right, main_bottom = main["bbox"]
    keep_box = (
        main_left - margin,
        main_top - margin,
        main_right + margin,
        main_bottom + margin,
    )

    cleaned = image.copy()
    output_pixels = cleaned.load()
    removed = False
    for component in components:
        if component is main:
            continue

        left, top, right, bottom = component["bbox"]
        overlaps_keep_box = not (
            right < keep_box[0]
            or left > keep_box[2]
            or bottom < keep_box[1]
            or top > keep_box[3]
        )
        if overlaps_keep_box:
            continue

        for x, y in component["pixels"]:
            red, green, blue, _alpha = output_pixels[x, y]
            output_pixels[x, y] = (red, green, blue, 0)
        removed = True

    return cleaned if removed else image


def fit_to_frame(
    image,
    dx=0,
    dy=0,
    clean_lower_artifacts=False,
    clean_remote_artifacts=True,
    anchor_bottom=False,
    scale_override=None,
):
    image = trim_alpha(image).convert("RGBA")
    max_w = FRAME_SIZE[0] - 28
    max_h = FRAME_SIZE[1] - 28
    scale = scale_override if scale_override is not None else min(max_w / image.width, max_h / image.height)
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    image = image.resize(size, Image.Resampling.LANCZOS)

    frame = Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0))
    x = (FRAME_SIZE[0] - image.width) // 2 + dx
    if anchor_bottom:
        y = FRAME_SIZE[1] - image.height - 14 + dy
    else:
        y = (FRAME_SIZE[1] - image.height) // 2 + dy
    frame.alpha_composite(image, (x, y))
    if clean_remote_artifacts:
        frame = remove_remote_artifacts(frame)
    if clean_lower_artifacts:
        frame = remove_detached_lower_artifacts(frame)
    return frame


def clear_state_dir(path):
    path.mkdir(parents=True, exist_ok=True)
    for frame in path.glob("frame_*.png"):
        frame.unlink()


def build_custom_walking_frames():
    """Load a real 8-frame walking cycle when a dedicated sheet is present."""
    if not WALKING_SHEET_PATH.exists():
        return None

    walking_sheet = Image.open(WALKING_SHEET_PATH).convert("RGBA")
    frame_count = WALKING_GRID[0] * WALKING_GRID[1]
    raw_frames = [
        trim_alpha(crop_cell(walking_sheet, index, WALKING_GRID)).convert("RGBA")
        for index in range(frame_count)
    ]

    # Use one shared scale for the whole gait. Per-frame fitting makes tucked
    # legs appear larger and extended legs appear smaller, which looks like the
    # entire sprite is pulsing instead of walking.
    max_w = FRAME_SIZE[0] - 28
    max_h = FRAME_SIZE[1] - 28
    widest = max(frame.width for frame in raw_frames)
    tallest = max(frame.height for frame in raw_frames)
    shared_scale = min(max_w / widest, max_h / tallest)

    return [
        fit_to_frame(
            frame,
            clean_lower_artifacts=True,
            anchor_bottom=True,
            scale_override=shared_scale,
        )
        for frame in raw_frames
    ]


def main():
    sheet = Image.open(SHEET_PATH).convert("RGBA")
    pose_images = {name: crop_cell(sheet, index) for name, index in POSES.items()}
    custom_walking_frames = build_custom_walking_frames()
    standing = trim_alpha(pose_images["idle_stand"])
    shared_scale = min(276 / standing.width, 280 / standing.height)
    # The sleeping pose is wider; all poses still use the same physical scale.
    shared_scale = min(shared_scale, 292 / max(trim_alpha(img).width for img in pose_images.values()))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for state, frames in STATE_FRAMES.items():
        state_dir = OUTPUT_DIR / state
        clear_state_dir(state_dir)

        if state == "walking" and custom_walking_frames:
            for i, frame in enumerate(custom_walking_frames):
                frame.save(state_dir / f"frame_{i:03d}.png")
            continue

        for i, spec in enumerate(frames):
            pose_name, dx, dy = spec
            frame = fit_to_frame(
                pose_images[pose_name],
                dx,
                dy,
                clean_lower_artifacts=(state == "walking"),
                scale_override=shared_scale,
                anchor_bottom=True,
            )
            frame.save(state_dir / f"frame_{i:03d}.png")

    print(f"Wrote {sum(len(v) for v in STATE_FRAMES.values())} frames to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
