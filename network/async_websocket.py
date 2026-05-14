import sys
sys.path.append('..')

import asyncio
import websockets
from observability.logger import 

class AsyncWebSocketServer():
    def __init__(self, callback, pre_message, port):
        self.callback=callback
        self.pre_message=pre_message
        self.__port = port
        self.__loop = None

    async def handler(websocket):
        self.loop = asyncio.get_running_loop()
        async for message in websocket:
            if pre_message is not None:
                self.response(self.pre_message, websocket)
            self.callback({'conn' : websocket, 'msg' : message})

    async def start_server():
        async with websockets.serve(handler, "localhost", self.__port):
            await asyncio.Future()

    def response(self, message, websocket):
        asyncio.run_coroutine_threadsafe(
            websocket.send(message), self.__loop
        )

    def start(self):
        asyncio.get_event_loop().run_until_complete(start_server())
        asyncio.get_event_loop().run_forever()

    def shutdown(self):
        pass


class AsyncWebSocketClient():
    def __init__(self, port):
        self.__uri = "ws://localhost:%s" % port
        self.__loop = asyncio.new_event_loop()
        self.__conn = None
        self.__thread = threading.Thread(target=self.__run_loop)
        self.__ready = threading.Event()
        self.__run = True
        self.__thread.start()

    def __run_loop(self):
        asyncio.set_event_loop(self.__loop)
        self.__loop.run_until_complete(self.__create_conn())

    def get_target_uri(self):
        return self.__uri

    async def __create_conn(self):
        try:
            async with websockets.connect(self.__uri) as websocket:
                self.conn = websocket
                self.__ready.set()
                #保持和复用当前连接
                while self.__run:
                    await asyncio.sleep(0.1)
        except Exception as e:
            log('CLIENT_CREATE_CONN_ERROR', e)
            self.__ready.set()
            raise

    def send(self, msg, callback):
        future = Future()
        async def __send():
            try:
                await self.conn.send(msg)
                resp = await self.conn.recv()
                while 'FINAL:' not in resp:
                    callback(resp)
                    time.sleep(0.1)
                    resp = await self.conn.recv()
                future.set_result(resp.replace('FINAL:', ''))
            except Exception as e:
                log('CLIENT_SEND_MSG_ERROR', e)
                future.set_exception(e)
        asyncio.run_coroutine_threadsafe(_send(), self._loop)
        return future.result()

    def shutdown(self):
        self.__run = False
        if self.conn:
            asyncio.run_coroutine_threadsafe(self.conn.close(), self.__loop)
        self.__thread.join(timeout=5)