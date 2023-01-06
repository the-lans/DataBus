from fastapi import Request
import pickle
import json
from aiohttp import ClientTimeout, ClientSession
from aiohttp.client_exceptions import ClientResponseError
from urllib.parse import urljoin
from typing import Dict, List, Optional

from backend.library.api import parse_api_exclude, parse_api_filter, dict_to_str_api, string_format_api
from backend.library.func import dict_to_str
from backend.library.logger import MainLogger
from backend.tasks.map import HTTPMapData
from backend.tasks.common_headers import HTTPHeadersData
from backend.db.base import create, execute
from backend.models.map import HTTPMapInDB
from backend.models.requests import RequestsInDB
from backend.models.user import UserInDB
from backend.models.verdict import VerdictInDB


class RequestMessage:
    def __init__(self, queue=None, method=None, url=None, headers=None, params_dict=None, params_other=None, body=None):
        self.req_in_db: List[RequestsInDB] = []
        self.queue = queue
        self.method = method
        self.initial_url = url
        self.proxy_urls: Dict[int, HTTPMapInDB] = {}
        self.headers = headers if headers else {}
        self.params_dict = params_dict if params_dict else {}
        self.params_other = params_other if params_other else {}
        self.body = body
        self.processed = False

    async def get_from_request(self, req: Request) -> 'RequestMessage':
        self.method = req.method
        self.initial_url = req.url.path
        self.headers = dict(req.headers)
        params_keys = req.query_params.getlist('params')
        query_params = parse_api_exclude(dict(req.query_params), {'params'})
        self.params_dict = parse_api_filter(query_params, set(params_keys))
        self.params_other = parse_api_exclude(query_params, set(params_keys))
        if req.method.lower() in ['post', 'put', 'patch']:
            body = await req.body()
            self.body = body if body else None
        return self

    def set_proxy_url(self, queue: str):
        self.queue = queue
        self.proxy_urls = HTTPMapData.filter(queue=queue, method=self.method)

    async def create_verdicts(self, user: UserInDB, status: str = 'new'):
        change_status = False
        if not self.req_in_db:
            for obj_map in self.proxy_urls.values():
                req_obj = await create(
                    RequestsInDB,
                    **{
                        'user': user,
                        'map': obj_map,
                        'data': dict_to_str_api(self.params_dict),
                        'queue': self.queue,
                        'params': dict_to_str_api(self.params_dict),
                        'last_status': status,
                    },
                )
                self.req_in_db.append(req_obj)
            change_status = True

        for obj_req in self.req_in_db:
            await self.create_verdict(obj_req, status, change_status)

    @staticmethod
    async def create_verdict(obj_req: RequestsInDB, status: str, change_status: bool = False):
        if status == 'new' or obj_req.last_status != status:
            await create(VerdictInDB, **{'req': obj_req, 'status': status})
            obj_req.last_status = status
            if not change_status:
                await execute(RequestsInDB.update(last_status=status).where(RequestsInDB.id == obj_req.id))

    def get_process_url(self, req: RequestsInDB) -> str:
        return urljoin(req.map.address, string_format_api(req.map.url, self.params_dict))

    async def send_requests(self) -> (int, str):
        timeout = ClientTimeout(total=60)
        results = []
        self.processed = True
        async with ClientSession() as sess:
            for obj_req in self.req_in_db:
                last_status = obj_req.last_status
                if last_status == 'delivered':
                    results.append((200, None))
                    continue

                try:
                    headers = self.headers.copy()
                    headers.update(HTTPHeadersData.filter_dict(queue=obj_req.queue))
                    async with sess.request(
                        self.method,
                        self.get_process_url(obj_req),
                        ssl=False,
                        raise_for_status=True,
                        timeout=timeout,
                        headers=headers if headers else None,
                        params=self.params_other if self.params_other else None,
                        data=self.body,
                    ) as resp:
                        last_status = 'delivered'
                        res = (resp.status, await resp.text())
                except ClientResponseError as e:
                    self.processed = False
                    last_status = 'fail'
                    res = (e.status, e.message)
                except Exception as e:
                    self.processed = False
                    last_status = 'fail'
                    res = (0, 'Failed to get content: %s' % e)

                await self.create_verdict(obj_req, last_status, False)
                results.append(res)
        return results

    def dumps(self) -> bytes:
        return pickle.dumps(self)

    @staticmethod
    def loads(obj: bytes) -> 'RequestMessage':
        return pickle.loads(obj)

    def log_write(self, response: Optional[dict] = None):
        _logger_print = MainLogger.main_logger().info
        _sep = '\n   '
        _logger_print(f"----------- Request {id(self)} -----------")
        _logger_print(f"Queue: {self.queue}")
        _logger_print(f"Method: {self.method}")
        _logger_print(f"Initial URL: {self.initial_url}")
        _proxy_urls = [self.get_process_url(obj_req) for obj_req in self.req_in_db]
        if _proxy_urls:
            _logger_print(f"Proxy URLs: {str(_proxy_urls)}")
        if self.headers:
            _headers = dict_to_str(self.headers, sep=_sep)
            _logger_print(f"Headers: {_sep}{_headers}")
        if self.params_dict:
            _params_dict = dict_to_str(self.params_dict, sep=_sep, sformat='{:} = {:}')
            _logger_print(f"Params for bus: {_sep}{_params_dict}")
        if self.params_other:
            _params_other = dict_to_str(self.params_other, sep=_sep, sformat='{:} = {:}')
            _logger_print(f"Params for proxy: {_sep}{_params_other}")
        if self.body:
            _logger_print(f"Body: {self.body}")
        if response:
            _logger_print(f"Response: {json.dumps(response)}")
