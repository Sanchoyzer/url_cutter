from sqlalchemy import Column, String
from sqlalchemy.schema import CheckConstraint

from url_cutter.entities.model import ExpiringEntity


class ApiKey(ExpiringEntity):
    __table_args__ = (
        CheckConstraint('char_length(key) = 32', name='check_key_len'),
        {'schema': 'public'},
    )
    __tablename__ = 'api_key'

    key = Column(String, nullable=False, unique=True, index=True)
    owner = Column(String, nullable=False)
