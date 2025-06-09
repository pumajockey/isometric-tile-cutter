# Standard Library
import traceback
import os
import sys
from pathlib import Path

# Third Party
from PIL import Image, ImageDraw


def make_isotile_mask(width: int) -> 'Image':
    assert width % 4 == 0
    assert width >= 8

    height = width // 2

    diamond_image = Image.new("L", (width // 2, height), (0))
    draw = ImageDraw.Draw(diamond_image)

    # Draw tile with 45 degree edges
    draw.polygon(
        [
            (0, height//2),
            (width//4 - 1, 1),
            (width//4, 1),
            (width//2 - 1, height//2),
            (width//4, height - 1),
            (width//4 - 1, height - 1),
            (0, height//2),
        ],
        fill=255,
    )

    # Resize with double the width to make 30 degree edges
    mask_image = diamond_image.resize(
        (width, height),
        Image.NEAREST,
    )

    return mask_image


def draw_mask(main_image: 'Image', mask_image: 'Image', x: int, y: int) -> 'Image':
    main_image.paste(mask_image, (x, y))

    return main_image


def get_output_path(tile_width: int, image_width: int, image_height: int) -> str:
    folder = Path(os.path.dirname(os.path.realpath(sys.argv[0]))) / 'template'
    filename = '{0}tw_{1}x-{2}y.png'.format(tile_width, image_width, image_height)

    return str(folder / filename)


def main():
    tile_width = int(input("Input width of a tile: "))
    assert tile_width % 4 == 0

    image_width = int(input("Input width of the entire image: "))
    assert image_width % tile_width == 0

    image_height = int(input("Input height of the entire image: "))
    assert image_height % (tile_width // 2) == 0

    tile_height = tile_width // 2

    main_image = Image.new("L", (image_width, image_height), (0))
    mask_image = make_isotile_mask(tile_width)

    num_columns = image_width // tile_width
    num_rows = image_height // tile_height

    for y in range(num_rows):
        for x in range(num_columns):
            main_image = draw_mask(main_image, mask_image, x * tile_width, y * tile_height)

    output_path = get_output_path(tile_width, image_width, image_height)

    main_image.save(output_path)
    print("Saved to {0}".format(output_path))


if __name__ == '__main__':
    try:
        main()
    except ValueError as exc:
        print(exc)
    except Exception:
        traceback.print_exc()

input("Press any key to continue")
