"""Peewee migrations -- 002_MAP.py.
"""

from peewee import SQL, Model, AutoField, DateTimeField, TextField


def migrate(migrator, database, fake=False, **kwargs):
    @migrator.create_model
    class HTTPMapInDB(Model):
        id = AutoField()
        created = DateTimeField(constraints=[SQL('DEFAULT current_timestamp')])
        queue = TextField(null=False)
        address = TextField(null=False)
        url = TextField(null=False)

        class Meta:
            table_name = 'maps'


def rollback(migrator, database, fake=False, **kwargs):
    migrator.remove_model('maps')
