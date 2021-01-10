import pytest
from faker import Faker
from fastapi.testclient import TestClient
from redis import Redis
from sqlalchemy import create_engine
from sqlalchemy_utils import create_database, database_exists, drop_database

from url_cutter.entities.model import Model
from url_cutter.main import app
from url_cutter.settings import get_settings


@pytest.fixture(scope='session')
def settings():
    return get_settings()


@pytest.fixture(scope='session')
def web_client():
    return TestClient(app=app)


@pytest.fixture(scope='session')
def main_db_uri(settings):
    return settings.MAIN_DB_URI


@pytest.fixture(scope='session')
def cache_db_uri(settings):
    return settings.CACHE_DB_URI


@pytest.fixture(scope='session')
def main_engine(main_db_uri):
    return create_engine(main_db_uri, client_encoding='utf8', connect_args={'client_encoding': 'utf8'})


@pytest.fixture(scope='session')
def cache_engine(cache_db_uri):
    return Redis.from_url(url=cache_db_uri)


@pytest.fixture(scope='session', autouse=True)
def database(main_engine, cache_engine, main_db_uri):
    if database_exists(main_db_uri):
        drop_database(main_db_uri)
    cache_engine.flushall()

    create_database(main_db_uri)
    Model.metadata.create_all(bind=main_engine)

    yield

    cache_engine.flushall()
    drop_database(main_db_uri)


@pytest.fixture(scope='session')
def faker():
    return Faker()
