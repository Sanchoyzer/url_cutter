import logging

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration


def init_sentry(sentry_dsn: str) -> None:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[
            CeleryIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.WARNING),
            RedisIntegration(),
            SqlalchemyIntegration(),
        ],
    )
