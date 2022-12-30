import yaml
from os.path import abspath, join


class ArgParse:
    _detail: bool = False
    _port: int = 8100
    _srv_name: str = 'main'

    @classmethod
    def setter(cls, detail: bool, port: int = 8100, srv_name: str = 'main'):
        cls._detail = detail
        cls._port = port
        cls._srv_name = srv_name

    @classmethod
    def getter(cls, item: str):
        return getattr(cls, '_' + item, None)


DEFAULT_WORK_DIR = abspath(join(abspath(__file__), '../..'))
DATA_DIR = join(DEFAULT_WORK_DIR, 'data')

conf_filename = 'conf.yaml'

try:
    settings = yaml.safe_load(open(join(DEFAULT_WORK_DIR, conf_filename)))
except FileNotFoundError:
    settings = {}

SECRET_KEY = settings.get('SECRET_KEY', 'secret')
ALGORITHM = settings.get('ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = settings.get('ACCESS_TOKEN_EXPIRE_MINUTES', 1440)

DB_SETTINGS = settings.get('DB', {})
DB_DOMAIN = DB_SETTINGS.get('DOMAIN', '127.0.0.1')
DB_NAME = DB_SETTINGS.get('NAME', None)
DB_USER = DB_SETTINGS.get('USER', 'postgres')
DB_ASYNC = DB_SETTINGS.get('ASYNC', False)

REDIS_QUEUE = 'queue'
