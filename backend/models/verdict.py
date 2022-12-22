from peewee import ForeignKeyField

from backend.models.base import BaseItem
from backend.models.requests import RequestsInDB
from backend.db.base import BaseDBItem
from backend.db.fields import OptionsField


class VerdictInDB(BaseDBItem):
    req = ForeignKeyField(RequestsInDB, null=False)
    status = OptionsField(
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
            'status': self.status,
            'req': RequestsInDB.get_by_id(self.req.id).dict,
        }

    async def check(self):
        await super().check()
        if not self.status:
            self.status = 'new'

    class Meta:
        table_name = 'verdict'


"""
class Verdict(BaseItem):
    req: Requests
    status: str

    @property
    async def dict(self):
        return {...}
"""

Verdict = VerdictInDB.get_class('Verdict', BaseItem)
