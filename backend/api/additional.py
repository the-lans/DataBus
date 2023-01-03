from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from fastapi import File, UploadFile, Query
from hashlib import sha256
from uuid import uuid4
from datetime import datetime, timezone
from typing import Optional, List

from backend.app import app
from backend.api.base import BaseAppAuth
from backend.library.security import get_password_hash
from backend.library.common import random_string, date_to_dict


router = InferringRouter()
TAG_CLASS = "AdditionalApp"


@cbv(router)
class AdditionalApp(BaseAppAuth):
    @router.get("/api/common/hash", tags=[TAG_CLASS])
    async def get_hash(self, password: str):
        return {"success": True, 'hash': get_password_hash(password)}

    @router.get("/api/common/sha256", tags=[TAG_CLASS])
    async def get_sha256(self, data: str):
        return {"success": True, 'hash': sha256(data.encode('utf8')).hexdigest()}

    @router.post("/api/common/sha256", tags=[TAG_CLASS])
    async def post_sha256(self, file: UploadFile = File(...)):
        content = file.file.read()
        return {"success": True, 'hash': sha256(content).hexdigest()}

    @router.get("/api/common/timestamp", tags=[TAG_CLASS])
    async def get_timestamp(self, sformat='%Y-%m-%d %H:%M:%S'):
        stamp = datetime.fromtimestamp(datetime.now().timestamp(), timezone.utc).strftime(sformat)
        return {"success": True, 'timestamp': stamp}

    @router.get("/api/common/now", tags=[TAG_CLASS])
    async def get_datetime_now(self):
        dt_dict = date_to_dict(datetime.now(timezone.utc))
        dt_dict['tzinfo'] = str(dt_dict['tzinfo'])
        return {"success": True, 'timestamp': dt_dict}

    @router.get("/api/common/uuid", tags=[TAG_CLASS])
    async def get_uuid4(self):
        return {"success": True, 'uuid': uuid4()}

    @router.get("/api/common/srand", tags=[TAG_CLASS])
    async def get_random_string(self, size: int, chars: Optional[List[str]] = Query([], title="Get Random String")):
        return {"success": True, 'string': random_string(size, chars)}


app.include_router(router)
