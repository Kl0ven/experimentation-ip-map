# experimentation ip map

This experimentation tries to create a map of all IpV4.

The data comes from : https://www.kaggle.com/datasets/signalspikes/internet-port-scan-1
Inspiration from http://tom7.org/harder/

The resulting images are 65536 \* 65536 pixels

Here is the result:

[Map of the web](https://www.easyzoom.com/imageaccess/091318e0f1e04383b736fe280941ee0b)
[Map of the ignored ips](https://www.easyzoom.com/imageaccess/bea51f2c2b41441783275bcbbd3284dc)

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
iterator = IgnoreStore(IGNORE_PATH) # to map the ignored ip
```
