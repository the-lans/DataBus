import argparse
import uvicorn

from tests.api import *
from backend.config import ArgParse, DB_SETTINGS
from backend.library.func import str_to_bool


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--detail", required=False, help="Datail requests")
    parser.add_argument("--port", required=False, help="Server port")
    args = parser.parse_args()

    detail = str_to_bool(args.detail) if args.detail else False
    port = int(args.port) if args.port else 8100
    ArgParse.setter(detail, port=port, srv_name='receiver')

    uvicorn.run(app, host=DB_SETTINGS['DOMAIN'], port=port)
