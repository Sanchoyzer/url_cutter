from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings, HttpUrl, PostgresDsn, RedisDsn, confloat, conint


class AppSettings(BaseSettings):
    MAIN_DB_URI: PostgresDsn
    CACHE_DB_URI: RedisDsn

    ENGINE_POOL_PRE_PING: bool = True
    ENGINE_POOL_RECYCLE: conint(ge=-1) = -1
    ENGINE_POOL_SIZE: conint(ge=1) = 5
    ENGINE_MAX_OVERFLOW: conint(ge=1) = 10
    ENGINE_POOL_TIMEOUT: conint(ge=1) = 30

    SESSION_AUTOCOMMIT: bool = False
    SESSION_AUTOFLUSH: bool = False

    CELERY_BROKER: RedisDsn
    CELERY_BACKEND: RedisDsn
    CELERY_ALWAYS_EAGER: bool = False

    SENTRY_DSN: Optional[HttpUrl] = None

    STORAGE_URL: HttpUrl
    UID_LEN: conint(ge=2, le=8)

    URL_TTL_SEC: conint(ge=1)
    PERIOD_CLEARING_EXPIRED_URLS_SEC: confloat(ge=1)

    API_KEY_TTL_SEC: conint(ge=1)
    PERIOD_CLEARING_EXPIRED_API_KEYS_SEC: confloat(ge=1)

    class Config:
        case_sensitive = True
        env_file = '.env'


@lru_cache()
def get_settings() -> AppSettings:
    return AppSettings()
