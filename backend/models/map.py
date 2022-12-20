from peewee import TextField

from backend.models.base import BaseItem
from backend.db.base import BaseDBItem


class HTTPMapInDB(BaseDBItem):
    queue = TextField(null=False)  # str
    address = TextField(null=False)  # str
    url = TextField(null=False)  # str

    @property
    async def dict(self):
        return {
            'id': self.id,
            'created': self.created,
            'queue': self.queue,
            'address': self.address,
            'url': self.url,
        }

    class Meta:
        table_name = 'maps'


"""
class HTTPMap(BaseItem):
    queue: str
    address: str
    url: str

    @property
    async def dict(self):
        return {...}
"""

HTTPMap = HTTPMapInDB.get_class('HTTPMap', BaseItem)
