"""Extract connected typing-arm overlay layers.

The typing scene is drawn like BongoCat:
1. rest full-frame scene
2. live keyboard overlay
3. connected hand/arm layer from the rest/tap full-frame scene

The hand must always be above the live keyboard. Otherwise the keyboard layer
covers the resting hand and the user perceives the hand as hidden/transparent.
"""
from pathlib import Path

from PIL import Image, ImageDraw


BASE_PATH = Path("assets/blue_chibi/typing_mongocat_base.png")
TAP_PATH = Path("assets/blue_chibi/typing_mongocat_tap.png")
OUT_PATH = Path("assets/blue_chibi/typing_mongocat_tap_overlay.png")
REST_OUT_PATH = Path("assets/blue_chibi/typing_mongocat_rest_overlay.png")


def extract_overlay(source, out_path):
    """Keep the connected right-side sleeve/forearm/hand and remove table pixels."""
    source = source.convert("RGBA")
    width, height = source.size

    # Focus on the screen-right hand: this is the single hand that taps keys.
    region = Image.new("L", source.size, 0)
    draw = ImageDraw.Draw(region)
    draw.rectangle(
        (
            int(width * 0.53),
            int(height * 0.40),
            int(width * 0.78),
            int(height * 0.82),
        ),
        fill=255,
    )

    red, green, blue, alpha = source.split()
    red_px = red.load()
    green_px = green.load()
    blue_px = blue.load()
    alpha_px = alpha.load()
    region_px = region.load()

    mask = Image.new("L", source.size, 0)
    mask_px = mask.load()

    for y in range(height):
        for x in range(width):
            if not region_px[x, y] or alpha_px[x, y] < 10:
                continue

            r = red_px[x, y]
            g = green_px[x, y]
            b = blue_px[x, y]
            brightness = (r + g + b) / 3
            saturation = max(r, g, b) - min(r, g, b)

            # Keep colored sleeve/skin/outline. Drop very pale table/keyboard fill.
            if saturation > 18 or brightness < 155:
                mask_px[x, y] = alpha_px[x, y]

    overlay = source.copy()
    overlay.putalpha(mask)
    overlay.save(out_path)

    visible_pixels = sum(1 for pixel in overlay.getdata() if pixel[3] > 0)
    print(f"Wrote {out_path}")
    print(f"Size: {overlay.size}")
    print(f"Transparent corner: {overlay.getpixel((0, 0))}")
    print(f"Visible pixels: {visible_pixels}")


def main():
    base = Image.open(BASE_PATH).convert("RGBA")
    tap = Image.open(TAP_PATH).convert("RGBA")
    if tap.size != base.size:
        tap = tap.resize(base.size, Image.Resampling.LANCZOS)

    extract_overlay(base, REST_OUT_PATH)
    extract_overlay(tap, OUT_PATH)


if __name__ == "__main__":
    main()
