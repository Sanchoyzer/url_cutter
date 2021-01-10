import string
from datetime import datetime, timedelta
from random import SystemRandom
from typing import Optional

from sqlalchemy.orm import Session

from url_cutter.entities.url.model import Url
from url_cutter.entities.url.schema import UrlCreateRequest
from url_cutter.exceptions import UidAlreadyInUse


class UrlResource:
    __slots__ = ('__weakref__', 'main_db')

    def __init__(self, main_db: Session) -> None:
        self.main_db = main_db

    @staticmethod
    def _gen_uid(uid_len: int) -> str:
        return ''.join(
            SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(uid_len)
        )

    def _get_uid(self, obj_in: UrlCreateRequest, uid_len: int) -> str:
        if obj_in.custom_uid:
            if self.main_db.query(Url).filter_by(uid=obj_in.custom_uid).first():
                raise UidAlreadyInUse(f'uid "{obj_in.custom_uid}" is already in use')
            else:
                uid = obj_in.custom_uid
        else:
            while self.main_db.query(Url).filter_by(uid=(uid := self._gen_uid(uid_len))).first():
                pass
        return uid

    def create(self, obj_in: UrlCreateRequest, uid_len: int, ttl: int) -> Url:
        db_obj = Url(
            link=obj_in.url,
            uid=self._get_uid(obj_in=obj_in, uid_len=uid_len),
            expiry_at=datetime.utcnow() + timedelta(seconds=ttl),
        )
        self.main_db.add(db_obj)
        self.main_db.commit()
        return db_obj

    def get(self, uid: str) -> Optional[Url]:
        return self.main_db.query(Url).filter_by(uid=uid).first()

    def remove(self, uid: str) -> None:
        if db_obj := self.get(uid=uid):
            self.main_db.delete(db_obj)
            self.main_db.commit()

    @classmethod
    def remove_expired(cls, main_db: Session) -> int:
        count = main_db.query(Url).filter(Url.expiry_at < datetime.utcnow()).delete()
        main_db.commit()
        return count
