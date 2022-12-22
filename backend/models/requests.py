from peewee import TextField, ForeignKeyField

from backend.models.base import BaseItem
from backend.models.map import HTTPMapInDB
from backend.models.user import UserInDB
from backend.db.base import BaseDBItem
from backend.db.fields import OptionsField


class RequestsInDB(BaseDBItem):
    user = ForeignKeyField(UserInDB, null=False)
    map = ForeignKeyField(HTTPMapInDB, null=True)
    data = TextField(null=True)  # str
    queue = TextField(null=False)  # str
    params = TextField(null=True)  # str
    last_status = OptionsField(
        [
            'new',
            'delivered',
            'fail',
        ],
        default='new',
    )

    @property
    async def dict(self):
        return {
            'id': self.id,
            'created': self.created,
            'data': self.data,
            'queue': self.queue,
            'params': self.params,
            'last_status': self.last_status,
            'map': HTTPMapInDB.get_by_id(self.map.id).dict,
            'user': UserInDB.get_by_id(self.user.id).dict,
        }

    async def check(self):
        await super().check()
        if not self.last_status:
            self.last_status = 'new'

    class Meta:
        table_name = 'requests'


"""
class Requests(BaseItem):
    user: User
    map: HTTPMap
    data: Optional[str]
    queue: str
    params: Optional[str]
    last_status: str

    @property
    async def dict(self):
        return {...}
"""

Requests = RequestsInDB.get_class('Requests', BaseItem)
