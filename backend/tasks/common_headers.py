from backend.models.common_headers import CommonHeadersInDB
from backend.db.base import BaseDBCache


class HTTPHeadersData(BaseDBCache):
    _model = CommonHeadersInDB
