import os
import pytest
from aiohttp import web
from motor.motor_asyncio import AsyncIOMotorClient

from app import RESTHandler


@pytest.fixture
async def app():
    app = web.Application()
    return app


@pytest.fixture
async def db(loop):
    c = AsyncIOMotorClient(os.getenv("DATABASE_URL"), io_loop=loop)
    return c


async def test_main_handler_status_code_not_200(aiohttp_client, loop, app, db):
    rh = RESTHandler(db, loop)
    app.add_routes([web.get('/', rh.handle_main)])
    http_client = await aiohttp_client(app)
    resp = await http_client.get('/')
    assert resp.status != 200


async def test_main_handler_response_text(aiohttp_client, loop, app, db):
    rh = RESTHandler(db, loop)
    app.add_routes([web.get('/', rh.handle_main)])
    http_client = await aiohttp_client(app)
    resp = await http_client.get('/')
    text = await resp.text()
    assert "Forbidden" not in text


async def test_main_handler_response_text_correct(aiohttp_client, loop, app, db):
    rh = RESTHandler(db, loop)
    app.add_routes([web.get('/', rh.handle_main)])
    http_client = await aiohttp_client(app)
    resp = await http_client.get('/')
    text = await resp.text()
    assert "I'm a teapot" in text


async def test_items_handler_get_50_items(aiohttp_client, loop, app, db):
    rh = RESTHandler(db, loop)
    app.add_routes([web.get('/items', rh.handle_items)])
    http_client = await aiohttp_client(app)
    resp = await http_client.get('/items')
    json_resp = await resp.json()
    assert len(json_resp) == 50


async def test_items_handler_different_pages(aiohttp_client, loop, app, db):
    rh = RESTHandler(db, loop)
    app.add_routes([web.get('/items', rh.handle_items)])
    http_client = await aiohttp_client(app)
    resp1 = await http_client.get('/items?page=1')
    resp2 = await http_client.get('/items?page=11')
    json_resp1 = await resp1.json()
    json_resp2 = await resp2.json()
    assert json_resp1 != json_resp2


async def test_items_handler_page_zero(aiohttp_client, loop, app, db):
    rh = RESTHandler(db, loop)
    app.add_routes([web.get('/items', rh.handle_items)])
    http_client = await aiohttp_client(app)
    resp = await http_client.get('/items?page=0')
    json_resp = await resp.json()
    assert len(json_resp) == 50


async def test_items_handler_page_param_is_rubbish(aiohttp_client, loop, app, db):
    rh = RESTHandler(db, loop)
    app.add_routes([web.get('/items', rh.handle_items)])
    http_client = await aiohttp_client(app)
    resp = await http_client.get('/items?page=glutenisbad')
    json_resp = await resp.json()
    assert len(json_resp) == 50