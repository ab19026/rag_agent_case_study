

import asyncio
import websockets
import time
import queue
import threading

s = set()
q = queue.Queue()


def t_tun(websocket, message, loop):
    time.sleep(10)
    asyncio.run_coroutine_threadsafe(
        websocket.send(f"异步返回: {message}"), loop
    )

def callback(q):
    while True:
        try:
            if not q.empty():
                v = q.get()
                websocket = v[0]
                message = v[1]
                loop = v[2]
                if 'AA' in message:
                    asyncio.run_coroutine_threadsafe(
                        websocket.send(f"请等待异步线程返回: {message}"), loop
                    )
                    threading.Thread(target=t_tun, args=(websocket, message, loop, )).start()
                else:
                    asyncio.run_coroutine_threadsafe(
                        websocket.send(f"正常返回: {message}"), loop
                    )
                 也可以在这里加日志、记录等，主循环会随后执行 send
                print(f"[线程] 提交了 Echo 任务: {message}")
            time.sleep(0.1)
        except:
            raise
    

threading.Thread(target=callback, args=(q,)).start()


def add_queue(v):
    global q
    q.put(v)

async def echo(websocket):
    global q
    s.add(websocket)
    loop = asyncio.get_running_loop()
    async for message in websocket:
        print(dir(websocket))
        print(f"Received: {message}")
        print(len(s))
        add_queue((websocket, message, loop))
        await websocket.send(f"Echo: {message}")
         asyncio.ensure_future(
             asyncio.to_thread(callback, websocket, message, loop)
         )


async def start_server():
    async with websockets.serve(echo, "localhost", 9764):
        print("服务器已启动，监听端口 9764...")
        await asyncio.Future()

asyncio.get_event_loop().run_until_complete(start_server())
asyncio.get_event_loop().run_forever()





import websockets
import asyncio
import threading
from concurrent.futures import Future

class Client():
    def __init__(self):
        self.uri = "ws://localhost:9764"
        self.pub_conn = None
        self._loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.__run_loop)
        self._ready = threading.Event()
        self.thread.start()
    def __run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self.__create_conn())
    async def __create_conn(self):
        try:
            async with websockets.connect(self.uri) as websocket:
                self.pub_conn = websocket
                self._ready.set()
                while True:
                    #短暂休眠，避免空转。也可以接收消息，按需实现。
                    await asyncio.sleep(0.1)
        except Exception as e:
            self._ready.set()
            raise
    def send(self, msg):
        future = Future()
        async def _send():
            try:
                await self.pub_conn.send(msg)
                resp = await self.pub_conn.recv()
                if '请等待异步线程返回' in resp:
                    resp = await self.pub_conn.recv()
                future.set_result(resp)
            except Exception as e:
                future.set_exception(e)
        asyncio.run_coroutine_threadsafe(_send(), self._loop)
        return future.result()
    def close(self):
        if self.pub_conn:
            asyncio.run_coroutine_threadsafe(self.pub_conn.close(), self._loop)
        self.thread.join(timeout=5)

client = Client()



print(client.send())


 def sync():
     uri = "ws://localhost:8765"
     async def client():
         uri = "ws://localhost:8765"
         async with websockets.connect(uri) as websocket:
             for i in range(10):
                 await websocket.send("Hello, Server!")
                 response = await websocket.recv()
                 print(f"Received: {response}")
     asyncio.get_event_loop().run_until_complete(client())


 with websockets.connect(uri).send("Hello, Server!") as websocket:
     websocket.send("Hello, Server!")