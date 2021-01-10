import pytest
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy_utils import create_database, database_exists, drop_database

from url_cutter.connections import main_engine
from url_cutter.depends import get_cache_db
from url_cutter.entities.model import Model
from url_cutter.main import app
from url_cutter.settings import get_settings


@pytest.fixture(scope='session')
def settings():
    return get_settings()


@pytest.fixture(scope='session')
def web_client():
    return TestClient(app=app)


@pytest.fixture(scope='session', autouse=True)
def database(settings):
    cache_db = get_cache_db()
    main_db_uri = settings.MAIN_DB_URI

    if database_exists(main_db_uri):
        drop_database(main_db_uri)
    cache_db.flushall()

    create_database(main_db_uri)
    Model.metadata.create_all(bind=main_engine)

    yield

    cache_db.flushall()
    drop_database(main_db_uri)


@pytest.fixture(scope='session')
def faker():
    return Faker()
