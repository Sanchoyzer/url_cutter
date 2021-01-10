from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from typing import Iterator

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from url_cutter.cache import Cache, CacheSession
from url_cutter.connections import MainSession
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


def get_cache_db() -> Cache:
    CacheSession.echo(0)
    return CacheSession


def get_app_settings() -> AppSettings:
    return get_settings()


def check_api_key(
    authorization: str = Header(..., min_length=39, max_length=39),
    cache_db: Cache = Depends(get_cache_db),
):
    if (
        len(auth_list := authorization.split(' ')) != 2
        or auth_list[0] != 'ApiKey'
        or not (expiry_at := cache_db.get(prefix='api_key', key=auth_list[1]))
        or datetime.fromisoformat(expiry_at) < datetime.utcnow()
    ):
        raise AuthError('Invalid api key')
