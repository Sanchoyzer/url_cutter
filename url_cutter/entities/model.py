from sqlalchemy import Column, DateTime, Integer, text
from sqlalchemy.ext.declarative import as_declarative


@as_declarative()
class Model:
    pass


class Entity(Model):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False, server_default=text("(now() at time zone 'utc')"))


class ExpiringEntity(Entity):
    __abstract__ = True

    expiry_at = Column(DateTime, nullable=False)
