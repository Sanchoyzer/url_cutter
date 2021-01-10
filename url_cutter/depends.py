from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from typing import Iterator

from fastapi import Depends, Header
from redis import Redis
from sqlalchemy.orm import Session

from url_cutter.connections.pg import MainSession
from url_cutter.connections.redis import CacheSession
from url_cutter.entities.api_key.model import ApiKey
from url_cutter.exceptions import AuthError
from url_cutter.settings import AppSettings, get_settings


def get_main_db() -> Iterator[Session]:
    db = MainSession()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_main_db_() -> Session:
    db = MainSession()
    try:
        yield db
    finally:
        db.close()


def main_session(func):
    @wraps(func)
    def inner(*args, **kwargs):
        with get_main_db_() as session:
            return func(*args, session=session, **kwargs)

    return inner


def get_cache_db() -> Redis:
    CacheSession.echo(0)
    return CacheSession


def get_app_settings() -> AppSettings:
    return get_settings()


def check_api_key(
    authorization: str = Header(..., min_length=39, max_length=39),
    main_db: Session = Depends(get_main_db),
):
    if (
        len(auth_list := authorization.split(' ')) != 2
        or auth_list[0] != 'ApiKey'
        or not (api_key := main_db.query(ApiKey).filter_by(key=auth_list[1]).first())
        or api_key.expiry_at < datetime.utcnow()
    ):
        raise AuthError('Invalid api key')
