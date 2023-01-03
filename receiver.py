import argparse
import uvicorn

from tests.api import *
from backend.config import ArgParse, DB_SETTINGS
from backend.library.func import str_to_bool
from backend.library.logger import MainLogger


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--detail", required=False, help="Datail requests")
    parser.add_argument("--server", required=False, help="Server address")
    parser.add_argument("--port", required=False, help="Server port")
    args = parser.parse_args()

    detail = str_to_bool(args.detail) if args.detail else False
    server = args.server if args.server else DB_SETTINGS['DOMAIN']
    port = int(args.port) if args.port else DB_SETTINGS['PORT'] + 100

    ArgParse.setter(srv_name='receiver', detail=detail, server=server, port=port)
    MainLogger.update_main_logger()

    uvicorn.run(app, host=server, port=port)
