from backend.models.map import HTTPMapInDB
from backend.db.base import BaseDBCache


class HTTPMapData(BaseDBCache):
    _model = HTTPMapInDB
