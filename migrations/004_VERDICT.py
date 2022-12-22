"""Peewee migrations -- 004_VERDICT.py.
"""

from peewee import SQL, Model, AutoField, DateTimeField, ForeignKeyField
from backend.models.requests import RequestsInDB
from backend.db.fields import OptionsField


def migrate(migrator, database, fake=False, **kwargs):
    @migrator.create_model
    class VerdictInDB(Model):
        id = AutoField()
        created = DateTimeField(constraints=[SQL('DEFAULT current_timestamp')])
        req = ForeignKeyField(RequestsInDB, null=False, column_name='req_id', field='id')
        status = OptionsField(
            [
                'new',
                'delivered',
                'fail',
            ],
            default='new',
        )

        class Meta:
            table_name = 'verdict'


def rollback(migrator, database, fake=False, **kwargs):
    migrator.remove_model('verdict')
