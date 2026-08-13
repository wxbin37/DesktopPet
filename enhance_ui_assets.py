"""Build sharper high-DPI desktop-pet assets.

The app window is small in logical pixels, but macOS Retina displays render it
at 2x/3x device pixels. These assets are prebuilt around a 3x target so Qt does
not have to stretch low-resolution pixmaps during painting.
"""
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageOps


SOURCE_DIR = Path("assets/blue_chibi")
HD_DIR = Path("assets/blue_chibi_hd")

WINDOW_LOGICAL_SIZE = (220, 155)
HD_SCALE = 3
FULLBODY_SIZE = (WINDOW_LOGICAL_SIZE[1] * HD_SCALE, WINDOW_LOGICAL_SIZE[1] * HD_SCALE)
TYPING_SCENE_SIZE = (
    WINDOW_LOGICAL_SIZE[0] * HD_SCALE,
    WINDOW_LOGICAL_SIZE[1] * HD_SCALE,
)

STATE_DIRS = [
    "idle",
    "typing",
    "walking",
    "sleeping",
    "happy",
    "surprised",
    "wakeup",
    "dragging",
    "selfie",
]

TYPING_BASE = "typing_mongocat_base.png"
TYPING_TAP = "typing_mongocat_tap.png"
TYPING_REST_OVERLAY = "typing_mongocat_rest_overlay.png"
TYPING_TAP_OVERLAY = "typing_mongocat_tap_overlay.png"


def sharpen_rgba(image, radius=0.65, percent=130, threshold=2):
    """Sharpen a transparent anime-style PNG while preserving clean alpha."""
    image = image.convert("RGBA")
    sharpened = image.filter(
        ImageFilter.UnsharpMask(
            radius=radius,
            percent=percent,
            threshold=threshold,
        )
    )

    # Remove almost-invisible edge noise without making antialiased edges jagged.
    alpha = sharpened.getchannel("A").point(
        lambda value: 0 if value < 3 else (255 if value > 252 else value)
    )
    sharpened.putalpha(alpha)
    return bleed_transparent_rgb(sharpened)


def resize_rgba(image, size):
    """Resize RGBA with premultiplied alpha to avoid dark/dirty transparent edges."""
    image = image.convert("RGBA")
    red, green, blue, alpha = image.split()
    premultiplied = Image.merge(
        "RGBA",
        (
            ImageChops.multiply(red, alpha),
            ImageChops.multiply(green, alpha),
            ImageChops.multiply(blue, alpha),
            alpha,
        ),
    )
    resized = premultiplied.resize(size, Image.Resampling.LANCZOS)

    data = []
    for red_value, green_value, blue_value, alpha_value in resized.getdata():
        if alpha_value == 0:
            data.append((0, 0, 0, 0))
            continue

        data.append(
            (
                min(255, int(red_value * 255 / alpha_value + 0.5)),
                min(255, int(green_value * 255 / alpha_value + 0.5)),
                min(255, int(blue_value * 255 / alpha_value + 0.5)),
                alpha_value,
            )
        )

    output = Image.new("RGBA", resized.size)
    output.putdata(data)
    return bleed_transparent_rgb(output)


def bleed_transparent_rgb(image, iterations=2):
    """Fill fully transparent RGB with nearby edge colors so later scaling stays clean."""
    image = image.convert("RGBA")
    width, height = image.size
    pixels = list(image.getdata())

    for _ in range(iterations):
        next_pixels = pixels[:]
        changed = False

        for y in range(height):
            row = y * width
            for x in range(width):
                index = row + x
                if pixels[index][3] != 0:
                    continue

                red_sum = green_sum = blue_sum = count = 0
                for dy in (-1, 0, 1):
                    ny = y + dy
                    if ny < 0 or ny >= height:
                        continue
                    neighbor_row = ny * width
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx = x + dx
                        if nx < 0 or nx >= width:
                            continue

                        red_value, green_value, blue_value, alpha_value = pixels[neighbor_row + nx]
                        if alpha_value > 0:
                            red_sum += red_value
                            green_sum += green_value
                            blue_sum += blue_value
                            count += 1

                if count:
                    next_pixels[index] = (
                        int(red_sum / count),
                        int(green_sum / count),
                        int(blue_sum / count),
                        0,
                    )
                    changed = True

        pixels = next_pixels
        if not changed:
            break

    output = Image.new("RGBA", image.size)
    output.putdata(pixels)
    return output


def save_png(image, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)


def resize_square_frame(path, output_path):
    image = Image.open(path).convert("RGBA")
    resized = resize_rgba(image, FULLBODY_SIZE)
    enhanced = sharpen_rgba(resized, radius=0.7, percent=125, threshold=2)
    save_png(enhanced, output_path)


def resize_typing_scene(path, output_path):
    image = Image.open(path).convert("RGBA")
    fitted = ImageOps.fit(
        image,
        TYPING_SCENE_SIZE,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )
    fitted = bleed_transparent_rgb(fitted, iterations=3)
    enhanced = sharpen_rgba(fitted, radius=0.55, percent=118, threshold=2)
    save_png(enhanced, output_path)


def extract_hand_overlay(source_path, output_path, down_frame=False):
    """Extract the single screen-right hand/sleeve layer for keyboard tapping."""
    source = Image.open(source_path).convert("RGBA")
    width, height = source.size

    left = int(width * 0.53)
    top = int(height * 0.40)
    right = int(width * 0.78)
    bottom = int(height * (0.84 if down_frame else 0.82))

    red, green, blue, alpha = source.split()
    red_px = red.load()
    green_px = green.load()
    blue_px = blue.load()
    alpha_px = alpha.load()

    mask = Image.new("L", source.size, 0)
    mask_px = mask.load()

    for y in range(top, bottom):
        for x in range(left, right):
            a = alpha_px[x, y]
            if a < 10:
                continue

            r = red_px[x, y]
            g = green_px[x, y]
            b = blue_px[x, y]
            brightness = (r + g + b) / 3
            saturation = max(r, g, b) - min(r, g, b)

            # Keep colored hoodie/skin/outline; drop pale desk and keyboard fill.
            if saturation > 18 or brightness < 155:
                mask_px[x, y] = a

    overlay = source.copy()
    overlay.putalpha(mask)
    overlay = sharpen_rgba(overlay, radius=0.45, percent=115, threshold=2)
    save_png(overlay, output_path)

    visible = sum(1 for pixel in overlay.getdata() if pixel[3] > 0)
    print(f"{output_path}: {overlay.size}, visible={visible}, bbox={overlay.getchannel('A').getbbox()}")


def build_hd_assets():
    if not SOURCE_DIR.exists():
        raise FileNotFoundError(f"Missing source assets: {SOURCE_DIR}")

    for state in STATE_DIRS:
        source_state_dir = SOURCE_DIR / state
        if not source_state_dir.exists():
            continue

        for frame_path in sorted(source_state_dir.glob("*.png")):
            resize_square_frame(frame_path, HD_DIR / state / frame_path.name)

    resize_typing_scene(SOURCE_DIR / TYPING_BASE, HD_DIR / TYPING_BASE)
    resize_typing_scene(SOURCE_DIR / TYPING_TAP, HD_DIR / TYPING_TAP)
    extract_hand_overlay(HD_DIR / TYPING_BASE, HD_DIR / TYPING_REST_OVERLAY, down_frame=False)
    extract_hand_overlay(HD_DIR / TYPING_TAP, HD_DIR / TYPING_TAP_OVERLAY, down_frame=True)

    frame_count = len(list(HD_DIR.glob("**/*.png")))
    print(f"Built {frame_count} high-DPI PNG assets in {HD_DIR}")


if __name__ == "__main__":
    build_hd_assets()
