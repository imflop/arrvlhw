import asyncio
from asyncio import tasks
import aiohttp
from aiohttp import web
from aiohttp.client_ws import ClientWebSocketResponse
import logging
import json
import motor.motor_asyncio

from aiomisc.log import LogFormat, LogLevel, basic_config


basic_config(LogLevel.info, LogFormat.color, buffered=True)
log = logging.getLogger(__name__)


class WebSocketHandler:
    def __init__(self, url: str, loop=None) -> None:
        self.url = url
        self.loop = loop or asyncio.get_event_loop()
        self.session = None
        self.websocket = None
        self.client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://localhost:27017/vehicle')
        self.db = self.client.get_database()
    
    async def connect(self):
        self.session = aiohttp.ClientSession()
        self.websocket = await self.session.ws_connect(url=self.url)
        await self.listen()

    async def listen(self):
        log.info("Start receiveing data")
        async for message in self.websocket:
            if message.type == aiohttp.WSMsgType.TEXT:
                await self.on_data_received(message.data)
            elif message.type == aiohttp.WSMsgType.ERROR:
                log.error(f"Error: {message}")
                break
            elif message.type == aiohttp.WSMsgType.CLOSED:
                log.info("Connection closed")
                break
            else:
                log.error(f"Unknown message: {message}")
    
    async def on_data_received(self, data):
        try:
            item = json.loads(data)
            if not item.get('country'):
                item['country'] = "USA"
            await self.do_insert(item)
        except ValueError as err:
            log.debug(f"Given json is invalid: {err}")
    
    async def do_insert(self, item):
        if item:
            result = await self.db.components.insert_one(item)
            log.debug(f"Inserted: {result.inserted_id}")
    
    async def close(self):
        self.session.close()
        self.websocket.close()


async def handle(request):
    name = request.match_info.get('name', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)

async def web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="localhost", port=31337) 
    await site.start()
    log.info("Start API serving on: ")

async def main():
    _tasks = []
    event_loop = asyncio.get_event_loop()
    ws_handler = WebSocketHandler("ws://localhost:8080", event_loop)
    _tasks.append(asyncio.create_task(ws_handler.connect()))
    _tasks.append(asyncio.create_task(web_server()))
    await asyncio.gather(*_tasks)

if __name__ == "__main__":
    asyncio.run(main())
    # event_loop = asyncio.get_event_loop()
    # ws_handler = WebSocketHandler("ws://localhost:8080", event_loop)

    # try:
        # web.run_app(app, host="localhost", port=31337)
        # event_loop.run_until_complete(ws_handler.connect())
        
    # except KeyboardInterrupt:
    #     pass
    # finally:
    #     event_loop.run_until_complete(ws_handler.close())
    #     event_loop.close()
