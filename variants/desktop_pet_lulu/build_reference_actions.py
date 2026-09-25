"""Extract independently generated reference poses for the existing pet runtime.

Only generated sheets belong in art/reference_actions. User reference originals
are not inputs to this build and are never copied into the app or repository.
"""
from pathlib import Path
import json
from statistics import median

from PIL import Image

from build_fullbody_assets import alpha_components, crop_cell, align_walking_heads
from config import REFERENCE_ACTIONS
from enhance_ui_assets import resize_square_frame


ROOT = Path(__file__).resolve().parent


def anchor_looking_up_feet(frames):
    """Keep the planted lower body fixed while eyes, head and paws explore."""
    centers = []
    for frame in frames:
        feet = frame.getchannel("A").crop((0, 285, 320, 307))
        box = feet.getbbox()
        if not box:
            raise ValueError("Missing planted feet in looking-up frame")
        centers.append((box[0] + box[2]) / 2)
    target = median(centers)
    result = []
    for frame, center in zip(frames, centers):
        dx = round(target - center)
        left, _, right, _ = frame.getchannel("A").getbbox()
        if left + dx <= 0 or right + dx >= frame.width:
            raise ValueError("Foot alignment would crop the character")
        aligned = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        aligned.alpha_composite(frame, (dx, 0))
        result.append(aligned)
    return result


def register_pullup_bar(frames):
    """Reuse the generated bar layer so AI sheet registration cannot move it.

    Keep the separately drawn character pixels; translate them by their grip
    anchor. No per-pose scaling or body deformation is used.
    """
    bars = []
    characters = []
    for frame in frames:
        pixels = frame.load()
        def green(x, y):
            r, g, b, a = pixels[x, y]
            return a > 0 and g > r * 1.12 and g > b * 1.12
        counts = [sum(green(x, y) for x in range(60, 260)) for y in range(320)]
        rows = [y for y, count in enumerate(counts) if count >= max(counts) * .6]
        top, bottom = min(rows), max(rows)
        center = round(median(rows))
        prop = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        character = frame.copy()
        for y in range(320):
            for x in range(320):
                if (x < 65 or x > 255 or
                        (green(x, y) and (x < 75 or x > 245 or abs(y-center) <= 16))):
                    prop.putpixel((x, y), pixels[x, y])
                    character.putpixel((x, y), (0, 0, 0, 0))
        bars.append((prop, top, bottom, center))
        characters.append(character)
    fixed_bar, top, bottom, target = bars[0]
    # The first drawing's gripping fingers occlude short spans of the bar.
    # Extend its own horizontal material underneath the moving hand layer.
    for y in range(top, bottom + 1):
        sample = fixed_bar.getpixel((160, y))
        if sample[3] > 0:
            for x in range(42, 278):
                if fixed_bar.getpixel((x, y))[3] == 0:
                    fixed_bar.putpixel((x, y), sample)
    aligned = []
    for character, (_, _, _, center) in zip(characters, bars):
        dy = target - center
        if character.getchannel("A").getbbox()[1] + dy <= 0:
            raise ValueError("Pullup registration would crop the fruit")
        output = fixed_bar.copy()
        output.alpha_composite(character, (0, dy))
        aligned.append(output)
    return aligned


def clean_cell(cell):
    """Preserve substantial disconnected parts (fruit/bar), discard edge flecks."""
    cell = cell.convert("RGBA")
    components = alpha_components(cell, threshold=8)
    if not components:
        raise ValueError("Empty reference-action cell")
    minimum_area = max(20, max(c["area"] for c in components) * .001)
    alpha = Image.new("L", cell.size, 0)
    source = cell.getchannel("A").load()
    target = alpha.load()
    for component in components:
        if component["area"] >= minimum_area:
            for x, y in component["pixels"]:
                target[x, y] = source[x, y]
    cell.putalpha(alpha)
    return cell


def build_action(state):
    source = ROOT / "art" / "reference_actions" / f"{state}_sheet.png"
    sheet = Image.open(source).convert("RGBA")
    cells = [clean_cell(crop_cell(sheet, i, (2, 2))) for i in range(4)]
    boxes = [cell.getchannel("A").getbbox() for cell in cells]
    if any(l <= 0 or t <= 0 or r >= cell.width or b >= cell.height
           for cell, (l, t, r, b) in zip(cells, boxes)):
        raise ValueError(f"{state}: generated pose reaches a cell edge")
    # A single scale for the entire action keeps size changes out of animation.
    scale = min(280 / max(r-l for l, t, r, b in boxes),
                280 / max(b-t for l, t, r, b in boxes))
    frames = []
    for cell, box in zip(cells, boxes):
        sprite = cell.crop(box)
        sprite = sprite.resize((round(sprite.width * scale), round(sprite.height * scale)),
                               Image.Resampling.LANCZOS)
        frame = Image.new("RGBA", (320, 320), (0, 0, 0, 0))
        # For pullups the bar's base determines the bounding box: the bar stays
        # grounded while the character moves inside it as the elbows bend.
        frame.alpha_composite(sprite, ((320-sprite.width)//2, 306-sprite.height))
        frames.append(frame)
    if state in {"shy", "laughing"}:
        frames = align_walking_heads(frames)
    elif state == "looking_up":
        frames = anchor_looking_up_feet(frames)
    elif state == "pullups":
        frames = register_pullup_bar(frames)
    low = ROOT / "assets" / "blue_chibi" / state
    high = ROOT / "assets" / "blue_chibi_hd" / state
    low.mkdir(parents=True, exist_ok=True)
    high.mkdir(parents=True, exist_ok=True)
    for old in [*low.glob("frame_*.png"), *high.glob("frame_*.png")]:
        old.unlink()
    for index, frame in enumerate(frames):
        filename = f"frame_{index:03d}.png"
        frame.save(low / filename)
        resize_square_frame(low / filename, high / filename)
    return {"source_size": sheet.size, "source_boxes": boxes, "shared_scale": scale,
            "output_boxes": [frame.getchannel("A").getbbox() for frame in frames]}


def main():
    report = {}
    for state in REFERENCE_ACTIONS:
        report[state] = build_action(state)
        print(f"Built {state}: 4 independent poses, low and high DPI", flush=True)
    (ROOT / "art" / "reference_actions" / "build_report.json").write_text(
        json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
