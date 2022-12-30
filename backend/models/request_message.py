from fastapi import Request
import pickle
import json
from aiohttp import ClientTimeout, ClientSession
from aiohttp.client_exceptions import ClientResponseError
from urllib.parse import urljoin
from typing import Dict, List, Optional

from backend.library.api import parse_api_exclude, parse_api_filter, dict_to_str_api, string_format_api
from backend.library.func import dict_to_str
from backend.library.logger import MAIN_LOGGER
from backend.tasks.map import filter_proxy_url
from backend.tasks.common_headers import filter_headers
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
        self.proxy_urls: Dict[HTTPMapInDB] = {}
        self.headers = headers if headers else {}
        self.params_dict = params_dict if params_dict else {}
        self.params_other = params_other if params_other else {}
        self.body = body
        self.processed = False

    def get_from_request(self, req: Request) -> 'RequestMessage':
        self.method = req.method
        self.initial_url = req.url.path
        self.headers = dict(req.headers)
        params_keys = req.query_params.getlist('params')
        query_params = parse_api_exclude(dict(req.query_params), {'params'})
        self.params_dict = parse_api_filter(query_params, set(params_keys))
        self.params_other = parse_api_exclude(query_params, set(params_keys))
        if req.method.lower() in ['post', 'put', 'patch']:
            body = req.body()
            self.body = body if body else None
        return self

    def set_proxy_url(self, queue: str):
        self.queue = queue
        self.proxy_urls = filter_proxy_url(queue, self.method)

    async def create_verdicts(self, user: UserInDB, status: str = 'new'):
        change_status = False
        if not self.req_in_db:
            for obj_map in self.proxy_urls.values():
                self.req_in_db.append(
                    await create(
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
                )
            change_status = True

        for obj_req in self.req_in_db:
            await self.create_verdict(obj_req, status, change_status)

    @staticmethod
    async def create_verdict(obj_req: RequestsInDB, status: str, change_status: bool = False):
        if obj_req.last_status != status:
            await create(VerdictInDB, **{'req': obj_req, 'status': status})
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
                if obj_req.status == 'delivered':
                    results.append((200, None))
                    continue

                try:
                    headers = self.headers.copy()
                    headers.update(filter_headers(obj_req.queue))
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
                        obj_req.status = 'delivered'
                        res = (resp.status, await resp.text())
                except ClientResponseError as e:
                    self.processed = False
                    obj_req.status = 'fail'
                    res = (e.status, e.message)
                except Exception as e:
                    self.processed = False
                    obj_req.status = 'fail'
                    res = (0, 'Failed to get content: %s' % e)

                await self.create_verdict(obj_req, obj_req.status)
                results.append(res)
        return results

    def dumps(self) -> bytes:
        return pickle.dumps(self)

    @staticmethod
    def loads(obj: bytes) -> 'RequestMessage':
        return pickle.loads(obj)

    def log_write(self, response: Optional[dict] = None):
        _logger_print = MAIN_LOGGER.info
        _logger_print(f"----------- Request {id(self)} -----------")
        _logger_print(f"Queue: {self.queue}")
        _logger_print(f"Method: {self.method}")
        _logger_print(f"Initial URL: {self.initial_url}")
        _proxy_urls = [self.get_process_url(obj_req) for obj_req in self.req_in_db]
        if _proxy_urls:
            _logger_print(f"Proxy URLs: {str(_proxy_urls)}")
        if self.headers:
            _headers = dict_to_str(self.headers, sep='\n')
            _logger_print(f"Headers: \n{_headers}")
        if self.params_dict:
            _params_dict = dict_to_str(self.params_dict, sep='\n', sformat='{:} = {:}')
            _logger_print(f"Params for bus: \n{_params_dict}")
        if self.params_other:
            _params_other = dict_to_str(self.params_other, sep='\n', sformat='{:} = {:}')
            _logger_print(f"Params for proxy: \n{_params_other}")
        if self.body:
            _logger_print(f"Body: {self.body}")
        if response:
            _logger_print(f"Response: {json.dumps(response)}")
