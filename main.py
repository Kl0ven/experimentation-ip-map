from hilbertcurve.hilbertcurve import HilbertCurve
from ipaddress import ip_address
from PIL import Image
from tqdm import tqdm
from ignore import IgnoreStore
from PIL import Image, ImageColor
import json
from enum import Enum

size_p = 16
IGNORE_PATH = "data/ignores.txt"
MASSCAN_FILE = "data/all_result.json"
GUESS_IP_NUMBER = 382_994_783  # for tqdm

COLORS = [
    "#239741",
    "#1F9B78",
    "#1B899F",
    "#174BA4",
    "#1F12A8",
    "#630EAC",
    "#AF0AB0",
    "#B40666",
    "#B80213",
    "#BD4300",
    "#C19D00",
    "#8CC500",
]


class ImageMode(Enum):
    BLACK_AND_WHITE = 1
    GRADIENT = 2


def compute_image(img, iterator, mode: ImageMode):
    hc = HilbertCurve(size_p, 2)

    for line in tqdm(iterator, total=GUESS_IP_NUMBER):
        ip = ip_address(line["ip"])
        point = tuple(hc.point_from_distance(ip._ip))

        if mode == ImageMode.GRADIENT:
            img.putpixel(point, img.getpixel(point) + 1)
        else:
            img.putpixel(point, 1)
    return img


def update_palette(img, colors):
    palette = img.getpalette()
    for i, color in enumerate(colors):
        index = (i + 1) * 3
        r, g, b = ImageColor.getrgb(color)
        palette[index] = r
        palette[index + 1] = g
        palette[index + 2] = b
    img.putpalette(palette)


def iterate_file(file_path):
    with open(file_path) as file:
        for line in file:
            if line.startswith("{"):
                line = json.loads(line)
                yield line


def create_image(mode):

    img = Image.new(
        "P" if mode == ImageMode.GRADIENT else "1", (2**size_p, 2**size_p)
    )

    if mode == ImageMode.GRADIENT:
        update_palette(img, COLORS)
    return img


def save_images(img, *args):
    for file in args:
        try:
            img.save(file)
        except Exception as err:
            print(err)


if __name__ == "__main__":
    mode = ImageMode.BLACK_AND_WHITE
    ignore = IgnoreStore(IGNORE_PATH)
    img = create_image(mode)
    iterator = iterate_file(MASSCAN_FILE)  # to map ip
    compute_image(img, iterator, mode, ignore)

    if mode == ImageMode.GRADIENT:
        ignore.annotate_image(img, HilbertCurve(size_p, 2), color=128)

    save_images(img, "out/all.png", "out/all.tiff")
