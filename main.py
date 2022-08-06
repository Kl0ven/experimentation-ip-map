import os
import signal
import tqdm
from netaddr import iter_iprange, IPAddress
import argparse
from pymongo import MongoClient
import asyncio
import aioping

FIELDS_NAMES = ["ip", "error", "timeout", "unknown_host", "response_time"]


def ip_range_generator(config):
    gen = iter_iprange(config.start_ip, config.end_ip, step=config.BATCH_SIZE)
    for ip in gen:
        end_ip = ip + (config.BATCH_SIZE - 1)
        end_ip_capped = end_ip if end_ip < config.end_ip else config.end_ip
        yield ip, end_ip_capped


class WorkItem:
    def __init__(self, config, start, end) -> None:
        self.config = config
        self.start = start
        self.end = end
        self.result = []

    def add_result(self, result):
        self.result.append(result)

    def get_range(self):
        return iter_iprange(self.start, self.end)

    def finish(self):
        self.config.collection.insert_many(self.result)


async def worker(name, queue: asyncio.Queue, pbar, stop):
    pbar.write(f"{name} stared")
    while True:
        # Get a ip range out of the queue.
        work_item: WorkItem = await queue.get()
        for ip in work_item.get_range():
            if stop.is_set():
                return
            ip_str = str(ip)
            result = {
                "ip": ip.value,
                "error": None,
                "timeout": False,
                "unknown_host": False,
                "response_time": None,
            }
            try:
                resp = await aioping.ping(ip_str, timeout=1)
                if resp is None:
                    result["timeout"] = True
                elif not resp:
                    result["unknown_host"] = True
                else:
                    result["response_time"] = resp * 1000
            except OSError as err:
                result["error"] = str(err)
            finally:
                work_item.add_result(result)
                pbar.update()

        work_item.finish()
        queue.task_done()


class GracefulKiller:
    kill_now = False

    def __init__(self, event):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        self.event = event

    def exit_gracefully(self, *args):
        self.kill_now = True
        self.event.set()


async def run(config):
    ips = ip_range_generator(config)
    stop = asyncio.Event()
    pbar = tqdm.tqdm(total=config.end_ip.value - config.start_ip.value, smoothing=0)
    killer = GracefulKiller(stop)

    queue = asyncio.Queue(maxsize=config.POOL_SIZE + config.OVER_FEEDING)

    workers = [
        asyncio.create_task(worker(f"worker {i}", queue, pbar, stop))
        for i in range(config.POOL_SIZE)
    ]

    for ip in ips:
        if killer.kill_now:
            pbar.write("Stopping; Waiting for completion")
            break
        try:
            queue.put_nowait(WorkItem(config, *ip))
        except asyncio.QueueFull:
            await asyncio.sleep(0.1)

    # Cancel our worker tasks.
    for w in workers:
        w.cancel()
    # Wait until all worker tasks are cancelled.
    await asyncio.gather(*workers)


def get_start_ip(collection):
    value = collection.find_one({}, sort=[("ip", -1)])
    if value:
        return IPAddress(value["ip"] + 1)
    return IPAddress(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ping the web")
    parser.add_argument("collection_name", type=str, default="ip")
    parser.add_argument("--mongo_host", type=str, default="localhost")
    parser.add_argument("--mongo_port", type=str, default="27017")
    parser.add_argument("--POOL_SIZE", "-ps", type=int, default=5)
    parser.add_argument("--BATCH_SIZE", "-bs", type=int, default=2000)
    parser.add_argument("--OVER_FEEDING", "-of", type=int, default=5)
    parser.add_argument("--DATA_FOLDER", "-f", type=str, default="data")
    args = parser.parse_args()
    client = MongoClient(f"mongodb://{args.mongo_host}:{args.mongo_port}")
    args.collection = client.ping_the_web[args.collection_name]
    args.start_ip = get_start_ip(args.collection)
    args.end_ip = IPAddress("255.255.255.255")
    os.makedirs(args.DATA_FOLDER, exist_ok=True)
    asyncio.run(run(args))
