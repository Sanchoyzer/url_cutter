from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from url_cutter.cache import Cache
from url_cutter.entities.api_key.model import ApiKey


class ApiKeyResource:
    __slots__ = ('__weakref__', 'main_db', 'cache_db', 'cache_prefix')

    def __init__(self, main_db: Session, cache_db: Cache) -> None:
        self.main_db = main_db
        self.cache_db = cache_db
        self.cache_prefix = 'api_key'

    def create(self, key: str, owner: str, ttl: int) -> ApiKey:
        db_obj = ApiKey(key=key, owner=owner, expiry_at=datetime.utcnow() + timedelta(seconds=ttl))
        self.main_db.add(db_obj)
        self.main_db.commit()
        self.cache_db.add(prefix=self.cache_prefix, key=db_obj.key, value=db_obj.expiry_at, ex=ttl)
        return db_obj

    @classmethod
    def remove_expired(csl, main_db: Session) -> int:
        count = main_db.query(ApiKey).filter(ApiKey.expiry_at < datetime.utcnow()).delete()
        main_db.commit()
        return count
