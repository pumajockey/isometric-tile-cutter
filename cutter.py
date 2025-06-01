# Standard Library
import sys
import traceback
from pathlib import Path
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


class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __mul__(self, scalar):
        return Point(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar):
        return Point(self.x * scalar, self.y * scalar)


class Rect(object):
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def __add__(self, other):
        return Rect(
            self.x1 + other.x1,
            self.y1 + other.y1,
            self.x2 + other.x2,
            self.y2 + other.y2,
        )

    def to_tuple(self) -> tuple:
        return (self.x1, self.y1, self.x2, self.y2)


class IsometricTileSize(object):
    def __init__(self, width: int):
        if width % 4 != 0:
            raise ValueError("Tile width must be a multiple of 4")

        self.width = width

    @property
    def height(self) -> int:
        return self.width // 2

    @property
    def half_width(self) -> int:
        return self.width // 2

    @property
    def half_height(self) -> int:
        return self.width // 4


class TiledImage(object):
    def __init__(self, path: str, tile_width: int):
        self.tile_size = IsometricTileSize(tile_width)

        image = Image.open(path)
        self.image_size = Point(*image.size)

        if self.image_size.x % self.tile_size.width != 0:
            raise ValueError("Input image width must be divisible by {0}".format(self.tile_size.width))
        if self.image_size.y % self.tile_size.height != 0:
            raise ValueError("Input image height must be divisible by {0}".format(self.tile_size.height))

        self.doubled_image = self.double_image(image)
        self.doubled_image_size = Point(*self.doubled_image.size)

    def __iter__(self):
        for y in range(self.num_rows):
            for x in range(self.num_columns):
                yield self.get_isotile(x, y)

    @property
    def num_rows(self) -> int:
        return (self.image_size.y // self.tile_size.height) * 2

    @property
    def num_columns(self) -> int:
        return self.image_size.x // self.tile_size.width

    def double_image(self, image: 'Image') -> 'Image':
        # Tile the image for easily getting partial tiles as a single whole tile
        # Eg the four corners of reference image are a single tile

        image_size = Point(*image.size)
        doubled_size = image_size * 2
        doubled_image = Image.new("RGBA", (doubled_size.x, doubled_size.y))

        doubled_image.paste(image, (0, 0))
        doubled_image.paste(image, (image_size.x, 0))
        doubled_image.paste(image, (0, image_size.y))
        doubled_image.paste(image, (image_size.x, image_size.y))

        return doubled_image

    def get_isotile(self, x: int, y: int) -> Image:
        # Starting position (tile[0][0])
        box = Rect(
            (self.doubled_image_size.x / 2) - self.tile_size.half_width,
            (self.doubled_image_size.y / 2) - self.tile_size.half_height,
            (self.doubled_image_size.x / 2) + self.tile_size.half_width,
            (self.doubled_image_size.y / 2) + self.tile_size.half_height,
        )

        # Shift box to x, y
        box += Rect(
            self.tile_size.width * x, self.tile_size.half_height * y,
            self.tile_size.width * x, self.tile_size.half_height * y,
        )

        # Shift half a tile right if an odd column
        if y % 2 == 1:
            box += Rect(
                self.tile_size.half_width, 0,
                self.tile_size.half_width, 0,
            )

        rect_image = self.doubled_image.crop(box.to_tuple())
        mask = make_isotile_mask(width=self.tile_size.width)
        transparent_image = Image.new("RGBA", rect_image.size, (0, 0, 0, 0))

        return Image.composite(rect_image, transparent_image, mask)


def process_image(path: 'Path', tile_width: int):
    tiled_image = TiledImage(str(path), tile_width)

    output_dir = Path(path).parent / "{0}".format(path.stem)
    output_dir.mkdir()
    print("Outputting to {0}".format(output_dir))

    tile_index = 1
    for isotile in tiled_image:
        output_path = output_dir / '{0}_{1}.png'.format(path.stem, tile_index)
        isotile.save(str(output_path))
        tile_index += 1


def main():
    if len(sys.argv) < 2:
        raise ValueError("Missing input file. ")

    tile_width = int(input("Input width of a tile: "))

    for arg in sys.argv[1:]:
        path = Path(arg)

        process_image(
            path=path,
            tile_width=tile_width,
        )


if __name__ == '__main__':
    try:
        main()
    except ValueError as exc:
        print(exc)
    except Exception:
        traceback.print_exc()

input("Press any key to continue")
