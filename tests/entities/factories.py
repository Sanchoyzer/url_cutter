from factory import Faker, fuzzy
from factory.alchemy import SQLAlchemyModelFactory

from url_cutter.depends import get_main_db
from url_cutter.entities.api_key.model import ApiKey
from url_cutter.entities.url.model import Url


class ModelFactory(SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = next(get_main_db())
        sqlalchemy_session_persistence = 'commit'


class UrlFactory(ModelFactory):
    class Meta:
        model = Url

    expiry_at = Faker('future_datetime')
    link = Faker('url')
    uid = fuzzy.FuzzyText(length=6)


class ApiKeyFactory(ModelFactory):
    class Meta:
        model = ApiKey

    expiry_at = Faker('future_datetime')
    key = fuzzy.FuzzyText(length=32)
    owner = fuzzy.FuzzyText()
