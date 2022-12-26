from peewee import TextField

from backend.models.base import BaseItem
from backend.db.base import BaseDBItem


class CommonHeadersInDB(BaseDBItem):
    queue = TextField(null=False)  # str
    key = TextField(null=False)  # str
    value = TextField(null=False)  # str

    @property
    async def dict(self):
        return {
            'id': self.id,
            'created': self.created,
            'queue': self.queue,
            'key': self.key,
            'value': self.value,
        }

    class Meta:
        table_name = 'commonheaders'


"""
class CommonHeaders(BaseItem):
    queue: str
    key: str
    value: str

    @property
    async def dict(self):
        return {...}
"""

CommonHeaders = CommonHeadersInDB.get_class('CommonHeaders', BaseItem)
