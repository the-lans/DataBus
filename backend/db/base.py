from datetime import datetime
from typing import Optional
from playhouse.pool import PooledSqliteExtDatabase
from peewee_async import Manager
from peewee import (
    ForeignKeyField,
    TextField,
    BooleanField,
    IntegerField,
    FloatField,
    DoubleField,
    DateField,
    DateTimeField,
    AutoField,
    Proxy,
    Model,
)

from backend.config import DB_NAME, DB_ASYNC
from backend.library.func import FieldHidden
from backend.db.fields import OptionsField

db = Proxy()
db.initialize(
    PooledSqliteExtDatabase(
        DB_NAME,
        max_connections=8,
        autorollback=True,
    )
)
manager = Proxy()
manager.initialize(Manager(db))


class BaseDBModel(Model):
    id = AutoField(help_text='Unique id of an object', _hidden=FieldHidden.WRITE)
    swagger_ignore = True
    not_editable = ['id']

    async def check(self):
        pass

    @classmethod
    def get_name(cls, postfix: Optional[str] = None):
        if postfix is None:
            return f'{cls.__name__.lower()}'
        else:
            return f'{cls.__name__.lower()}_{postfix}'

    @classmethod
    def get_cls_dict(cls, kwargs):
        return {key: kwargs[key] for key in cls._meta.columns.keys() if key in kwargs}

    @classmethod
    async def update_or_create(cls, obj, obj_db=None, ret=None, return_obj_db=False):
        if ret is None:
            ret = {}
        obj_dict = cls.get_cls_dict(obj if isinstance(obj, dict) else await obj.dict)
        if obj_db is None:
            obj_db = cls(**obj_dict)
        else:
            for key, val in obj_dict.items():
                if key not in obj_db.not_editable:
                    setattr(obj_db, key, val)
        await obj_db.check()
        obj_db.save()
        ret.update(await obj_db.dict)
        if return_obj_db:
            return ret, obj_db
        else:
            return ret

    @classmethod
    def get_class(cls, name, parent, not_editable=None):
        conf = {
            ForeignKeyField: int,
            TextField: str,
            IntegerField: int,
            FloatField: float,
            DoubleField: float,
            BooleanField: bool,
            OptionsField: str,
            DateField: datetime,
            DateTimeField: datetime,
        }
        # class_val = {str: '', int: 0, float: 0.0, bool: False, datetime: datetime.strptime('1970-01-01', '%Y-%m-%d')}
        class_val = {str: '', int: 0, float: 0.0, bool: False, datetime: ''}
        res_type = {key.strip('_'): conf[type(val)] for key, val in cls._meta.columns.items() if type(val) in conf}
        if not_editable:
            res = {key: class_val[val] for key, val in res_type.items() if key not in not_editable}
        else:
            res = {key: class_val[val] for key, val in res_type.items()}

        @property
        async def get_dict(self):
            return {key: getattr(self, key) for key in res.keys()}

        res['dict'] = get_dict
        return type(name, (parent,), res)

    class Meta:
        database = db


class BaseDBItem(BaseDBModel):
    created = DateTimeField(default=datetime.now, _hidden=FieldHidden.WRITE)
    swagger_ignore = True
    not_editable = ['id', 'created']

    async def check(self):
        await super().check()
        if not self.created:
            self.created = datetime.now()


async def execute(query, *args, **kwargs):
    return await manager.execute(query, *args, **kwargs) if DB_ASYNC else query.execute(*args, **kwargs)


async def get_or_create(query, *args, **kwargs):
    return await manager.get_or_create(query, *args, **kwargs) if DB_ASYNC else query.get_or_create(*args, **kwargs)


async def create(query, *args, **kwargs):
    return await manager.create(query, *args, **kwargs) if DB_ASYNC else query.create(*args, **kwargs)
