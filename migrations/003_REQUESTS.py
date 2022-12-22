"""Peewee migrations -- 003_REQUESTS.py.
"""

from peewee import SQL, Model, AutoField, DateTimeField, TextField, ForeignKeyField
from backend.models.map import HTTPMapInDB
from backend.models.user import UserInDB
from backend.db.fields import OptionsField


def migrate(migrator, database, fake=False, **kwargs):
    @migrator.create_model
    class RequestsInDB(Model):
        id = AutoField()
        created = DateTimeField(constraints=[SQL('DEFAULT current_timestamp')])
        user = ForeignKeyField(UserInDB, null=False, column_name='user_id', field='id')
        map = ForeignKeyField(HTTPMapInDB, null=True, column_name='map_id', field='id')
        data = TextField(null=True)
        queue = TextField(null=False)
        params = TextField(null=True)
        last_status = OptionsField(
            [
                'new',
                'delivered',
                'fail',
            ],
            default='new',
        )

        class Meta:
            table_name = 'requests'


def rollback(migrator, database, fake=False, **kwargs):
    migrator.remove_model('requests')
