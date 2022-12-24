"""Peewee migrations -- 005_MAP_METHOD.py.
"""

from peewee import TextField


def migrate(migrator, database, fake=False, **kwargs):
    migrator.add_fields('maps', method=TextField(null=False, default=''))


def rollback(migrator, database, fake=False, **kwargs):
    migrator.remove_fields('maps', 'method')
