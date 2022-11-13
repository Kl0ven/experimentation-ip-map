# experimentation ip map

This experimentation tries to create a map of all IpV4.

The data comes from : https://www.kaggle.com/datasets/signalspikes/internet-port-scan-1

or more recent : https://www.kaggle.com/datasets/jeanloupmonnier/internet-scan

Inspiration from http://tom7.org/harder/

The resulting images are 65536 \* 65536 pixels

Here is the result:

[Map of the web](https://www.easyzoom.com/imageaccess/091318e0f1e04383b736fe280941ee0b)

[Map of the web in colors](https://www.easyzoom.com/imageaccess/f7ab163bf3de4c1caa6707d6996b46bb)

[Map of the ignored ips](https://www.easyzoom.com/imageaccess/bea51f2c2b41441783275bcbbd3284dc)

[Full map 2022 and ignored ip in orange](https://www.easyzoom.com/imageaccess/0e2da761880c4d89b8d0e7e65445c928)

## usage

```bash
poetry install
poetry run main.py # compute then save images in out
```

configuration in `main.py`

```python
IGNORE_PATH = "data/ignores.txt" # path to ignored ips
MASSCAN_FILE = "data/scan-04_27_2021-1619562631-C17RqCX0.json" # path to masscan result.json
GUESS_IP_NUMBER = 64802621  # for tqdm to give an ETA, can be safely ignore


iterator = iterate_file(MASSCAN_FILE)  # to map ip

# to map the ignored ip
ignore = IgnoreStore(IGNORE_PATH)
# will use draw.rectangle to map full network at once
ignore.annotate_image(img, HilbertCurve(size_p, 2), color=128)
```
