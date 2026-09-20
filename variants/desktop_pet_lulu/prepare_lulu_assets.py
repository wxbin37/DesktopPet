"""Extract Lulu's generated poses for the existing DesktopPet asset pipeline."""
from pathlib import Path
from PIL import Image
from build_fullbody_assets import alpha_components, crop_cell

ROOT = Path(__file__).resolve().parent


def clean_character(image):
    image = image.convert('RGBA')
    main = max(alpha_components(image, threshold=8), key=lambda c: c['area'])
    alpha = Image.new('L', image.size, 0)
    source, target = image.getchannel('A').load(), alpha.load()
    for x, y in main['pixels']:
        target[x, y] = source[x, y]
    image.putalpha(alpha)
    return image


def main():
    sheet = Image.open(ROOT/'art/fullbody_generated.png').convert('RGBA')
    cells = [clean_character(crop_cell(sheet, i)) for i in range(12)]
    # The original sheet crossed a row boundary at the mandarin stem.
    # Replace that pose from the uncropped, separately generated source.
    drag = clean_character(Image.open(ROOT/'art/dragging_generated.png'))
    drag = drag.crop(drag.getchannel('A').getbbox())
    stand_height = cells[0].getchannel('A').getbbox()[3] - cells[0].getchannel('A').getbbox()[1]
    factor = stand_height / drag.height
    drag = drag.resize((round(drag.width*factor),round(drag.height*factor)), Image.Resampling.LANCZOS)
    cells[10] = Image.new('RGBA',cells[10].size)
    cells[10].alpha_composite(drag, ((cells[10].width-drag.width)//2,(cells[10].height-drag.height)//2))
    clean_sheet = Image.new('RGBA', sheet.size)
    for i, cell in enumerate(cells):
        clean_sheet.alpha_composite(cell, (round(sheet.width*(i%4)/4), round(sheet.height*(i//4)/3)))
    clean_sheet.save(ROOT/'art/fullbody_sprite_sheet_alpha.png')

    typing = Image.open(ROOT/'art/typing_generated.png').convert('RGBA')
    base = ROOT/'assets/blue_chibi'
    base.mkdir(parents=True, exist_ok=True)
    for i, name in enumerate(['base','tap']):
        frame = clean_character(crop_cell(typing, i, (2,1)))
        frame.save(base/f'typing_mongocat_{name}.png')


if __name__ == '__main__':
    main()
