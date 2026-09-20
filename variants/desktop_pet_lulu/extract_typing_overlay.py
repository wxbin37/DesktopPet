"""Separate the generated left paw from the static Lulu typing scene."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops

BASE = Path('assets/blue_chibi')


def arm_mask(scene):
    width, height = scene.size
    region = Image.new('L', scene.size, 0)
    ImageDraw.Draw(region).polygon([(int(x*width),int(y*height)) for x,y in [
        (.700,.615),(.750,.630),(.790,.700),(.790,.820),
        (.630,.820),(.630,.700),(.660,.650)]], fill=255)
    rp = region.load()
    sp = scene.load()
    for y in range(height):
        for x in range(width):
            if not rp[x,y]:
                continue
            r,g,b,a = sp[x,y]
            # Yellow fur, including shading, but neither orange muzzle nor pale desk.
            rp[x,y] = a if a > 8 and g > r*.71 and g-b > 32 and r-b > 40 else 0
    return region


def main():
    rest = Image.open(BASE/'typing_mongocat_base.png').convert('RGBA')
    tap = Image.open(BASE/'typing_mongocat_tap.png').convert('RGBA')
    assert rest.size == tap.size
    rest_mask, tap_mask = arm_mask(rest), arm_mask(tap)
    for scene, mask, name in [(rest,rest_mask,'rest'),(tap,tap_mask,'tap')]:
        layer = scene.copy()
        layer.putalpha(mask)
        layer.save(BASE/f'typing_mongocat_{name}_overlay.png')
    # A single immutable body/table layer ensures that only the left paw moves.
    body = rest.copy()
    pixels = body.load(); selected = rest_mask.load()
    width,height=body.size
    for y in range(height):
        for x in range(width):
            if selected[x,y]:
                if y >= height*.745:
                    pixels[x,y] = rest.getpixel((int(width*.82),y))
                else:
                    pixels[x,y] = (0,0,0,0)
    body.save(BASE/'typing_mongocat_base.png')
    # Keep this compatibility file static; the runtime uses the separate arm layers.
    body.save(BASE/'typing_mongocat_tap.png')
    print('Separated static typing scene and two connected left-arm poses')


if __name__ == '__main__':
    main()
