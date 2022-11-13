from hilbertcurve.hilbertcurve import HilbertCurve
from PIL import Image
from ignore import IgnoreStore
from PIL import Image


size_p = 16
IGNORE_PATH = "data/ignores.txt"


palette = [0, 0, 0, 255, 138, 102] + [255, 255, 255] * 254

Image.MAX_IMAGE_PIXELS = 41073741824
img = Image.open("out/big data set/all.png").convert("P")

img.putpalette(palette)

ignore = IgnoreStore(IGNORE_PATH)
ignore.annotate_image(img, HilbertCurve(size_p, 2), color=1)

img.save("out/full.png")
