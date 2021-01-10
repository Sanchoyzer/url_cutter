import pytest
from sqlalchemy.orm import sessionmaker

from url_cutter.entities.api_key.resource import ApiKeyResource


@pytest.fixture(scope='session')
def request_headers():
    return [
        ('host', 'testserver'),
        ('user-agent', 'testclient'),
        ('accept-encoding', 'gzip, deflate'),
        ('accept', '*/*'),
        ('connection', 'keep-alive'),
    ]


@pytest.fixture(scope='session')
def client(faker):
    return {'host': faker.ipv4(), 'port': str(faker.port_number(is_user=True))}


@pytest.fixture()
def api_key(faker, main_engine, settings):
    res = ApiKeyResource(main_db=sessionmaker(autocommit=False, autoflush=False, bind=main_engine)())
    key = faker.pystr(min_chars=32, max_chars=32)
    return res.create(key=key, owner='test', ttl=settings.API_KEY_TTL_SEC)


@pytest.fixture()
def headers(faker, api_key):
    return {'Authorization': f'ApiKey {api_key.key}', 'User-Agent': faker.user_agent()}
