import queue
import sys, os, time
from concurrent.futures import ThreadPoolExecutor
sys.path.append('..')
from util.io import *

queue = Queue()

app_conf = parse_json_file('../conf/app.json')

run=False

def log(msg)
    global queue
    queue.put(msg)

def persist():
    global queue
    buffer = []
    while run:
        if not queue.empty():
            buffer.append(queue.get())
            if buffer > app_conf['log_persist_buffer']:
                with open(app_conf['log_path'], 'wa') as f:
                    for line in buffer:
                        f.write(line + '\n')
                buffer = []
        time.sleep(0.1)


with ThreadPoolExecutor(max_workers=app_conf['max_worker_num']) as pool:
    global queue
    pool.submit(persist)