import os
import signal
from ping3 import ping
import tqdm 
import concurrent.futures
from netaddr import iter_iprange, IPAddress
import itertools
import argparse
from threading import Event
from pymongo import MongoClient


FIELDS_NAMES =  ["ip", "error", "timeout", "unknown_host", "response_time"]

def ip_range_generator(config):
    gen = iter_iprange(config.start_ip, config.end_ip, step=config.BATCH_SIZE)
    for ip in gen:
        end_ip = ip + (config.BATCH_SIZE - 1)
        end_ip_capped = end_ip if end_ip < config.end_ip else config.end_ip
        yield ip, end_ip_capped


def run_one_batch(pbar, config, stop, start, end):
    rows = []
    for ip in iter_iprange(start, end):
        if stop.is_set():
            return
        ip_str = str(ip)
        result = {
            "ip": ip.value,
            "error": None,
            "timeout": False,
            "unknown_host": False,
            "response_time": None
        }
        try:
            resp = ping(ip_str, unit="ms", timeout=1)
            if resp is None:
                result["timeout"] = True
            elif not resp:
                result["unknown_host"] = True
            else:
                result["response_time"] = resp
        except OSError as err:
            result["error"] = str(err)
        finally:
            rows.append(result)
            pbar.update()

    config.collection.insert_many(rows)



class GracefulKiller:
    kill_now = False
    def __init__(self, event):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        self.event = event 
    def exit_gracefully(self, *args):
        self.kill_now = True
        self.event.set()

def run(config):
    ips = ip_range_generator(config)
    stop = Event()
    pbar = tqdm.tqdm(total=config.end_ip.value - config.start_ip.value, smoothing=0)
    killer = GracefulKiller(stop)
    with concurrent.futures.ThreadPoolExecutor(max_workers=config.POOL_SIZE) as executor:
        # Start the load operations and mark each future with its ip range
        # over feeding to reduce downtime
        future_to_index = {executor.submit(run_one_batch, pbar, config, stop, *ip): ip for ip in itertools.islice(ips, config.POOL_SIZE + config.OVER_FEEDING)}
        while future_to_index:
            done, _ = concurrent.futures.wait(
                future_to_index, timeout=0.25,
                return_when=concurrent.futures.FIRST_COMPLETED)
            
            for future in done:
                # for debug
                future.result()
                next_range = next(ips, None)
                if next_range:
                    future_to_index[executor.submit(run_one_batch, pbar, config, stop, *next_range)] = next_range
                del future_to_index[future]
            
            if killer.kill_now:
                pbar.write("Stopping; Waiting for completion")
                break

def get_start_ip(collection):
    value = collection.find_one({}, sort=[("ip", -1)])
    if value:
        return IPAddress(value["ip"]+1)
    return IPAddress(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ping the web")
    parser.add_argument("collection_name", type=str, default="ip")
    parser.add_argument("--mongo_host", type=str, default="localhost")
    parser.add_argument("--mongo_port", type=str, default="27017")
    parser.add_argument("--POOL_SIZE", "-ps", type=int, default=200)
    parser.add_argument("--BATCH_SIZE", "-bs", type=int, default=100)
    parser.add_argument("--OVER_FEEDING", "-of", type=int, default=5)
    parser.add_argument("--DATA_FOLDER", "-f", type=str, default="data")
    args = parser.parse_args()
    client = MongoClient(f"mongodb://{args.mongo_host}:{args.mongo_port}")
    args.collection = client.ping_the_web[args.collection_name]
    args.start_ip = get_start_ip(args.collection)
    args.end_ip = IPAddress("255.255.255.255")
    os.makedirs(args.DATA_FOLDER, exist_ok=True)
    run(args)