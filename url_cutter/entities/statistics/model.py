from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from url_cutter.entities.model import Entity


class Statistics(Entity):
    __table_args__ = {'schema': 'public'}
    __tablename__ = 'statistics'

    url_id = Column(Integer, ForeignKey('public.url.id', ondelete='CASCADE'), nullable=False, index=True)
    user_agent = Column(String)
    host = Column(String, nullable=False)

    url = relationship('Url', back_populates='statistics')
