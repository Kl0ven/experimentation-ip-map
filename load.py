from glob import iglob, glob
from pymongo import MongoClient
from csv import DictReader
from tqdm import tqdm
from netaddr import IPAddress
client = MongoClient("mongodb://localhost:27017")
db = client.ping_the_web

coll = db.ip_prod
coll.create_index("ip", unique=True)

pbar = tqdm(total=len(glob("data/**/*.csv", recursive=True)), smoothing=0.01)

BUFFER_SIZE = 10000


buffer = []
for file in iglob("data/**/*.csv", recursive=True):

    with open(file) as file:
        for entry in DictReader(file):
            entry['ip'] = IPAddress(entry['ip']).value
            if entry['error'] == "":
                entry['error'] = None
            entry["timeout"] = True if entry["timeout"] == "True" else False 
            entry["unknown_host"] = True if entry["unknown_host"] == "True" else False 
            if entry["response_time"] == "":
                entry["response_time"] = None
            else:
                entry["response_time"] = float(entry["response_time"])    
            buffer.append(entry)
        pbar.update()

    if len(buffer) > BUFFER_SIZE:    
        coll.insert_many(buffer)
        buffer = []

coll.insert_many(buffer)