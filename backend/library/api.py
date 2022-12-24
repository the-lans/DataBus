def parse_api_list(args: list[str]):
    fargs = []
    for item in args:
        fargs.extend(item.split())
    return fargs


def parse_api_exclude(data: dict, keys_exclude: list):
    return {key: value for key, value in data.items() if key not in keys_exclude}
