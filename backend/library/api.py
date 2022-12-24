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


def dict_to_str(data: dict, sep: str = ',') -> str:
    return sep.join([f'{key}={value}' for key, value in data.items()])
