from typing import Optional
from urllib.parse import urljoin

from backend.config import DB_SETTINGS


def parse_api_list(args: list[str]) -> list[str]:
    fargs = []
    for item in args:
        item_new = item.strip()
        if len(item_new) > 1 and item_new[0] == '"' and item_new[-1] == '"':
            fargs.append(item_new[1:-1])
        else:
            fargs.extend(item_new.split())
    return fargs


def parse_api_filter(data: dict, keys: set) -> dict:
    return {key: value for key, value in data.items() if key in keys}


def parse_api_exclude(data: dict, keys_exclude: set) -> dict:
    return {key: value for key, value in data.items() if key not in keys_exclude}


def dict_to_str_api(data: dict, sep: str = ',') -> str:
    return sep.join([f'{key}={value}' for key, value in data.items()])


def string_format_api(dformat: str, data: dict) -> str:
    newstr = dformat[:]
    for key, val in data.items():
        newstr = newstr.replace('{' + key + '}', str(val))
    return newstr


def databus_api(url: str, server: Optional[str] = None, port: Optional[int] = None, *fargs) -> str:
    server = server if server else DB_SETTINGS['DOMAIN']
    port = port if port else DB_SETTINGS['PORT']
    return 'http://' + server + ':' + str(port) + (urljoin(url, *fargs) if fargs else url)


def databus_params(url: str, fkwargs: dict, directly: bool = True, queue: str = 'test'):
    url = string_format_api(url, fkwargs) if directly else f'/api/queue/{queue}'
    params = None
    if not directly and fkwargs:
        params = {'params': list(fkwargs.keys())}
        params.update(fkwargs)
    return url, params


def union_dict(*args, is_none: bool = True):
    result = {}
    for item in args:
        if item:
            result.update(item)
    return result if result or not is_none else None
