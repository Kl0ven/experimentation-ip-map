from collections import defaultdict
import os
import signal
from ping3 import ping
import tqdm 
import concurrent.futures
from netaddr import iter_iprange
import itertools
from csv import DictWriter

POOL_SIZE = 100
BATCH_SIZE = 500
ROW_BUFFER = 100
OVER_FEEDING = 10
DATA_FOLDER = "data"
FIELDS_NAMES =  ["ip", "error", "timeout", "unknown_host", "response_time"]

def ip_range_generator():
    gen = iter_iprange('0.0.0.0', '255.255.255.255', step=BATCH_SIZE)
    for ip in gen:
        yield ip, ip + (BATCH_SIZE - 1)


def run_one_batch(pbar, start, end):
    file_name = f"{start}___{end}.csv"
    dir_path = os.path.join(DATA_FOLDER, str(start.words[0]), str(start.words[1]))
    file_path  = os.path.join(dir_path, file_name)
    if os.path.exists(file_path):
        pbar.write(f"file already exist {file_path}")
        return
    os.makedirs(dir_path, exist_ok=True)
    with open(file_path, "w", newline="") as csv_file:
        writer = DictWriter(csv_file, fieldnames=FIELDS_NAMES)
        writer.writeheader()
        rows = []
        for ip in iter_iprange(start, end):
            ip_str = str(ip)
            result = {
                "ip": ip_str,
                "error": None,
                "timeout": False,
                "unknown_host": False,
                "response_time": None
            }
            try:
                resp = ping(ip_str, unit="ms", timeout=2)
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
            
            if len(rows) >= ROW_BUFFER:
                writer.writerows(rows)
                rows = []
        writer.writerows(rows)



class GracefulKiller:
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        self.kill_now = True

def run():
    ips = ip_range_generator()
    pbar = tqdm.tqdm(total=255 ** 4)
    killer = GracefulKiller()
    with concurrent.futures.ThreadPoolExecutor(max_workers=POOL_SIZE) as executor:
        # Start the load operations and mark each future with its ip range
        # over feeding to reduce downtime
        future_to_index = {executor.submit(run_one_batch, pbar, *ip): ip for ip in itertools.islice(ips, POOL_SIZE + OVER_FEEDING)}
        while future_to_index:
            done, _ = concurrent.futures.wait(
                future_to_index, timeout=0.25,
                return_when=concurrent.futures.FIRST_COMPLETED)
            
            for future in done:
                # for debug
                future.result()
                next_range = next(ips)
                future_to_index[executor.submit(run_one_batch, pbar, *next_range)] = next_range
                pbar.update(BATCH_SIZE)
                del future_to_index[future]
            
            if killer.kill_now:
                pbar.write("Stopping; Waiting for completion")
                done, _ = concurrent.futures.wait(future_to_index, return_when=concurrent.futures.ALL_COMPLETED)
                break


if __name__ == "__main__":
    os.makedirs(DATA_FOLDER, exist_ok=True)
    run()