from typing import Optional, Dict
import argparse
from aiohttp import ClientTimeout, ClientSession
from aiohttp.client_exceptions import ClientResponseError
from random import randint
import json
import asyncio

from backend.config import ArgParse, DB_SETTINGS
from backend.library.api import databus_api, databus_params, union_dict
from backend.library.logger import MainLogger
from backend.library.func import str_to_bool


async def ftest_api(
    data: list[dict], directly: bool, srv: str, prt: int, uname: str, upass: str, num: int = 100
) -> Optional[Dict]:
    timeout = ClientTimeout(total=300)
    _logger = MainLogger.main_logger()
    result = None
    async with ClientSession() as sess:
        try:
            async with sess.post(
                databus_api('/login', srv, prt),
                ssl=False,
                raise_for_status=True,
                timeout=timeout,
                data={'username': uname, 'password': upass},
            ) as resp:
                result = await resp.json()
                req_headers = {'Authorization': f"{result['token_type']} {result['access_token']}"}

            async with sess.get(
                databus_api('/api/test/stat/start', srv, prt),
                ssl=False,
                raise_for_status=True,
                timeout=timeout,
                headers=req_headers,
            ):
                _logger.info("Start...")
                for _ in range(num):
                    await ftest_api_requests(sess, timeout, data, directly, srv, prt, req_headers)
                _logger.info("...Finish")

            async with sess.get(
                databus_api('/api/test/stat/slice', srv, prt),
                ssl=False,
                raise_for_status=True,
                timeout=timeout,
                headers=req_headers,
            ) as resp:
                result = await resp.json()
                if not (
                    result['success'] and all([result[key] == num for key in ['get_item', 'new_item', 'update_item']])
                ):
                    _logger.warning(f"Assert error!")
                _logger.info(f"Num: {num}")
                _logger.info(f"Result: {json.dumps(result)}")

        except ClientResponseError as e:
            _logger.error(f"Status: {e.status}, Message: {e.message}")

        except Exception as e:
            _logger.error('Failed to get content: %s' % e)

    return result


async def ftest_api_requests(
    sess: ClientSession,
    timeout: ClientTimeout,
    data: list[dict],
    directly: bool,
    srv: str,
    prt: int,
    req_headers: dict,
):
    for item in data:
        item_id = randint(1, 1000) if item['id'] else 0
        url, params_dict = databus_params(item['url'], {'item_id': item_id}, directly, 'test')
        req_params = union_dict(item.get('params', None), params_dict)
        if 'headers' in item:
            req_headers.update(item['headers'])
        async with sess.request(
            item['method'],
            databus_api(url, srv, prt),
            ssl=False,
            raise_for_status=False,
            timeout=timeout,
            headers=req_headers,
            params=req_params,
            data=item.get('body', None),
        ):
            pass


async def ftest_task(srv: str, prt: int, uname: str, upass: str, detail: bool):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/108.0.0.0 Mobile Safari/537.36',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    params = {'param1': 123, 'param2': 'Hello!'}
    body = {'query1': '044525225', 'query2': '044525235'}
    data_api = [
        {'method': 'get', 'url': '/api/test/{item_id}', 'id': True, 'headers': headers, 'params': params},
        {'method': 'put', 'url': '/api/test/{item_id}', 'id': True, 'headers': headers, 'params': params, 'body': body},
        {'method': 'post', 'url': '/api/test/new', 'id': False, 'headers': headers, 'params': params, 'body': body},
    ]

    await ftest_api(data_api, True, srv, prt, uname, upass, 1 if detail else 100)
    await ftest_api(data_api, False, DB_SETTINGS['DOMAIN'], DB_SETTINGS['PORT'], uname, upass, 1 if detail else 100)


async def ftest(srv: str, prt: int, uname: str, upass: str, detail: bool):
    task = asyncio.create_task(ftest_task(srv, prt, uname, upass, detail))
    await task


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--detail", required=False, help="Datail requests")
    parser.add_argument("--server", required=False, help="Server address")
    parser.add_argument("--port", required=False, help="Server port")
    parser.add_argument("--user", required=False, help="Username")
    parser.add_argument("--pass", required=False, help="Password")
    args = parser.parse_args()

    detail = str_to_bool(args.detail) if args.detail else False
    server = args.server if args.server else DB_SETTINGS['DOMAIN']
    port = int(args.port) if args.port else DB_SETTINGS['PORT'] + 100
    username = args.user if args.user else 'user'
    password = args.user if args.user else 'user'

    ArgParse.setter(srv_name='sender', server=server, port=port)
    MainLogger.update_main_logger()

    asyncio.run(ftest(server, port, username, password, detail))
