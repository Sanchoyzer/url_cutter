import logging
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from url_cutter.connections import celery, init_sentry
from url_cutter.depends import main_session
from url_cutter.entities.api_key.resource import ApiKeyResource
from url_cutter.entities.statistics.resource import StatisticsResource
from url_cutter.entities.url.resource import UrlResource
from url_cutter.settings import get_settings


settings = get_settings()
init_sentry(sentry_dsn=settings.SENTRY_DSN)


@celery.task
def clear_expired_urls() -> None:
    logging.info(f'clear_expired_urls, rows = {_clear_expired_urls()}')


@celery.task
def clear_expired_api_keys() -> None:
    logging.info(f'clear_expired_api_keys, rows = {_clear_expired_api_keys()}')


@celery.task
def update_statistics(url_uid: str, headers: List[Tuple[str, str]], client: Dict) -> None:
    if not _update_statistics(url_uid=url_uid, headers=headers, client=client):
        logging.warning(f'None result of "update_statistics", {url_uid=}')


@main_session
def _clear_expired_urls(session: Session) -> int:
    return UrlResource.remove_expired(main_db=session)


@main_session
def _clear_expired_api_keys(session: Session) -> int:
    return ApiKeyResource.remove_expired(main_db=session)


@main_session
def _update_statistics(
    url_uid: str, headers: List[Tuple[str, str]], client: Dict, session: Session
) -> Optional[int]:
    return StatisticsResource(main_db=session).update(uid=url_uid, headers=headers, client=client)
