from hilbertcurve.hilbertcurve import HilbertCurve
from ipaddress import ip_address
from PIL import Image
from tqdm import tqdm
from ignore import IgnoreStore

import json

size_p = 16
IGNORE_PATH = "data/ignores.txt"
MASSCAN_FILE = "data/scan-04_27_2021-1619562631-C17RqCX0.json"
GUESS_IP_NUMBER = 64802621  # for tqdm


def create_image(iterator):
    img = Image.new("1", (2**size_p, 2**size_p))
    hc = HilbertCurve(size_p, 2)
    for line in tqdm(iterator, total=GUESS_IP_NUMBER):
        ip = ip_address(line["ip"])
        point = hc.point_from_distance(ip._ip)
        img.putpixel(point, 1)
    return img


def iterate_file(file_path):
    with open(file_path) as file:
        for line in file:
            if line.startswith("{"):
                line = json.loads(line)
                yield line


if __name__ == "__main__":
    iterator = iterate_file(MASSCAN_FILE)  # to map ip
    # iterator = IgnoreStore(IGNORE_PATH) # to map the ignored ip
    img = create_image(iterator)
    # img.show()
    img.save("out/all.tiff")
    img.save("out/all.png")
