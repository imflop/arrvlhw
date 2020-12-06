import asyncio
from asyncio import tasks
import aiohttp
from aiohttp import web
from aiohttp.client_ws import ClientWebSocketResponse
import logging
import json
import motor.motor_asyncio
from bson import json_util

from aiomisc.log import LogFormat, LogLevel, basic_config


basic_config(LogLevel.info, LogFormat.color, buffered=True)
log = logging.getLogger(__name__)


class WebSocketHandler:
    def __init__(self, url: str, db_client, loop=None) -> None:
        self.url = url
        self.loop = loop or asyncio.get_event_loop()
        self.session = None
        self.websocket = None
        self.client = db_client
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


class RESTHandler:

    def __init__(self, db_client, loop=None) -> None:
        self.client = db_client
        self.loop = loop or asyncio.get_event_loop()
        self.db = self.client.get_database()
        self.page_size = 50
    
    def handle_main(self, request):
        kek = "I'm a teapot"
        return web.Response(text=kek, status=418)
    
    async def handle_item(self, request):
        page_num = request.query.get('page')
        if page_num:
            skips = self.page_size * (int(page_num) - 1)
        else:
            skips = 0
        cursor = self.db.components.find().skip(skips).limit(self.page_size)
        result = [document async for document in cursor]
        return web.Response(text=json.dumps(result, default=json_util.default))


async def web_server(handler):
    app = web.Application()
    app.add_routes([
        web.get('/', handler.handle_main),
        web.get('/items', handler.handle_item)
    ])
    runner = web.AppRunner(app)
    await runner.setup()
    api = web.TCPSite(runner, host="localhost", port=31337) 
    await api.start()
    log.info("Start API serving on: ")

async def main():
    _tasks = []
    event_loop = asyncio.get_event_loop()
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017/vehicle")
    rest_handler = RESTHandler(client, event_loop)
    ws_handler = WebSocketHandler("ws://localhost:8080", client, event_loop)
    _tasks.append(asyncio.create_task(ws_handler.connect()))
    _tasks.append(asyncio.create_task(web_server(rest_handler)))
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
