"""Peewee migrations -- 006_COMMON_HEADERS.py.
"""

from peewee import SQL, Model, AutoField, DateTimeField, TextField


def migrate(migrator, database, fake=False, **kwargs):
    @migrator.create_model
    class CommonHeadersInDB(Model):
        id = AutoField()
        created = DateTimeField(constraints=[SQL('DEFAULT current_timestamp')])
        queue = TextField(null=False, default='')
        key = TextField(null=False, default='')
        value = TextField(null=False, default='')

        class Meta:
            table_name = 'commonheaders'


def rollback(migrator, database, fake=False, **kwargs):
    migrator.remove_model('commonheaders')
