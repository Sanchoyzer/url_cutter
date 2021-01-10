from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from url_cutter.entities.api_key.model import ApiKey


class ApiKeyResource:
    __slots__ = ('__weakref__', 'main_db')

    def __init__(self, main_db: Session) -> None:
        self.main_db = main_db

    def create(self, key: str, owner: str, ttl: int) -> ApiKey:
        db_obj = ApiKey(key=key, owner=owner, expiry_at=datetime.utcnow() + timedelta(seconds=ttl))
        self.main_db.add(db_obj)
        self.main_db.commit()
        return db_obj

    def remove_expired(self) -> int:
        count = self.main_db.query(ApiKey).filter(ApiKey.expiry_at < datetime.utcnow()).delete()
        self.main_db.commit()
        return count
