#!/usr/bin/env python3
"""Build transparent full-body desktop pet frames from a 4x3 sprite sheet."""
from pathlib import Path

from PIL import Image


PROJECT_DIR = Path(__file__).resolve().parent
SHEET_PATH = PROJECT_DIR / "art" / "fullbody_sprite_sheet_alpha.png"
OUTPUT_DIR = PROJECT_DIR / "assets" / "blue_chibi"
FRAME_SIZE = (320, 320)
GRID = (4, 3)


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
    "idle": [
        ("idle_stand", 0, 0),
        ("idle_stand", 0, -2),
        ("idle_blink", 0, -1),
        ("idle_stand", 0, 0),
        ("idle_stand", 0, 1),
        ("idle_stand", 0, 0),
    ],
    "walking": [
        ("walk_a", 0, 2),
        ("walk_a", 0, -2),
        ("walk_b", 0, 1),
        ("walk_b", 0, -2),
        ("walk_a", 0, 2),
        ("walk_b", 0, 0),
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


def crop_cell(sheet, index):
    cols, rows = GRID
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
    """Return connected alpha components, used to remove detached floor shadows."""
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


def fit_to_frame(image, dx=0, dy=0, clean_lower_artifacts=False):
    image = trim_alpha(image).convert("RGBA")
    max_w = FRAME_SIZE[0] - 28
    max_h = FRAME_SIZE[1] - 28
    scale = min(max_w / image.width, max_h / image.height)
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    image = image.resize(size, Image.Resampling.LANCZOS)

    frame = Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0))
    x = (FRAME_SIZE[0] - image.width) // 2 + dx
    y = (FRAME_SIZE[1] - image.height) // 2 + dy
    frame.alpha_composite(image, (x, y))
    if clean_lower_artifacts:
        frame = remove_detached_lower_artifacts(frame)
    return frame


def clear_state_dir(path):
    path.mkdir(parents=True, exist_ok=True)
    for frame in path.glob("frame_*.png"):
        frame.unlink()


def main():
    sheet = Image.open(SHEET_PATH).convert("RGBA")
    pose_images = {name: crop_cell(sheet, index) for name, index in POSES.items()}

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for state, frames in STATE_FRAMES.items():
        state_dir = OUTPUT_DIR / state
        clear_state_dir(state_dir)
        for i, (pose_name, dx, dy) in enumerate(frames):
            frame = fit_to_frame(
                pose_images[pose_name],
                dx,
                dy,
                clean_lower_artifacts=(state == "walking"),
            )
            frame.save(state_dir / f"frame_{i:03d}.png")

    print(f"Wrote {sum(len(v) for v in STATE_FRAMES.values())} frames to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
