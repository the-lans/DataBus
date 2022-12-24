"""Peewee migrations -- 002_MAP.py.
"""

from peewee import SQL, Model, AutoField, DateTimeField, TextField


def migrate(migrator, database, fake=False, **kwargs):
    @migrator.create_model
    class HTTPMapInDB(Model):
        id = AutoField()
        created = DateTimeField(constraints=[SQL('DEFAULT current_timestamp')])
        queue = TextField(null=False, default='')
        address = TextField(null=False, default='127.0.0.1')
        url = TextField(null=False, default='')

        class Meta:
            table_name = 'maps'


def rollback(migrator, database, fake=False, **kwargs):
    migrator.remove_model('maps')
