from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from url_cutter.entities.model import ExpiringEntity


# TODO: set uid as PK?
class Url(ExpiringEntity):
    __table_args__ = {'schema': 'public'}
    __tablename__ = 'url'

    link = Column(String, nullable=False, index=True)
    uid = Column(String, nullable=False, unique=True, index=True)

    statistics = relationship('Statistics', cascade='all, delete', back_populates='url')
