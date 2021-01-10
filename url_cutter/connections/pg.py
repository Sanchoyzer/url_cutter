from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from url_cutter.settings import get_settings


settings = get_settings()

main_engine = create_engine(
    settings.MAIN_DB_URI,
    max_overflow=settings.ENGINE_MAX_OVERFLOW,
    pool_pre_ping=settings.ENGINE_POOL_PRE_PING,
    pool_size=settings.ENGINE_POOL_SIZE,
    pool_recycle=settings.ENGINE_POOL_RECYCLE,
    pool_timeout=settings.ENGINE_POOL_TIMEOUT,
)
MainSession = sessionmaker(
    autoflush=settings.SESSION_AUTOFLUSH, autocommit=settings.SESSION_AUTOCOMMIT, bind=main_engine
)
