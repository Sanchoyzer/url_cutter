import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from qrcode import make as make_qr
from qrcode.image.pil import PilImage
from requests.exceptions import ConnectionError
from sqlalchemy.orm import Session

from url_cutter.cache import Cache
from url_cutter.entities.statistics.model import Statistics
from url_cutter.entities.statistics.resource import StatisticsResource
from url_cutter.entities.url.model import Url
from url_cutter.entities.url.resource import UrlResource
from url_cutter.entities.url.schema import UrlCreateRequest
from url_cutter.exceptions import UrlAlreadyShort, UrlNotAvailable
from url_cutter.settings import AppSettings
from url_cutter.tasks.background import update_statistics


class CutterService:
    __slots__ = (
        '__weakref__',
        'main_db',
        'cache_db',
        'settings',
        'url_resource',
        'statistics_resource',
        'url_prefix',
        'uid_len',
        'url_ttl',
        'cache_prefix',
    )

    def __init__(self, main_db: Session, cache_db: Cache, settings: AppSettings) -> None:
        self.main_db = main_db
        self.cache_db = cache_db
        self.url_resource = UrlResource(main_db=main_db)
        self.statistics_resource = StatisticsResource(main_db=main_db)
        self.url_prefix = settings.STORAGE_URL
        self.uid_len = settings.UID_LEN
        self.url_ttl = settings.URL_TTL_SEC
        self.cache_prefix = 'url'

    def _add_to_cache(self, db_obj: Url, ex: int) -> bool:
        return self.cache_db.add(prefix=self.cache_prefix, key=db_obj.uid, value=db_obj.link, ex=ex)

    def _get_from_cache(self, uid: str) -> Optional[str]:
        return self.cache_db.get(prefix=self.cache_prefix, key=uid)

    @classmethod
    def _check_before_create(cls, obj_in: UrlCreateRequest, url_prefix: str) -> None:
        if urlparse(obj_in.url).netloc == urlparse(url_prefix).netloc:
            raise UrlAlreadyShort('url already short')

        try:
            requests.head(url=obj_in.url, timeout=1)
        except ConnectionError:
            raise UrlNotAvailable(f'url "{obj_in.url}" is not available')

    def create(self, obj_in: UrlCreateRequest) -> Tuple[str, datetime]:
        self._check_before_create(obj_in=obj_in, url_prefix=self.url_prefix)
        url = self.url_resource.create(obj_in=obj_in, uid_len=self.uid_len, ttl=self.url_ttl)
        self._add_to_cache(db_obj=url, ex=self.url_ttl)
        return self.url_prefix + url.uid, url.expiry_at

    def create_qr_code(self, obj_in: UrlCreateRequest) -> Tuple[PilImage, datetime]:
        short_url, expiry_at = self.create(obj_in=obj_in)
        return make_qr(data=short_url), expiry_at

    def get(self, uid: str, headers: List[Tuple[str, str]], client: Dict) -> Optional[str]:
        if cache_url := self._get_from_cache(uid=uid):
            update_statistics.delay(url_uid=uid, headers=headers, client=client)
            return cache_url

        if not (url := self.url_resource.get(uid=uid)):
            return None

        if (ttl_delta := url.expiry_at - datetime.utcnow()).total_seconds() > 0:
            logging.warning(f'{uid=} is out of cache but still actual')
            self._add_to_cache(db_obj=url, ex=ttl_delta)
            update_statistics.delay(url_uid=uid, headers=headers, client=client)
            return url.link
        else:
            self.url_resource.remove(uid=uid)
            return None

    def get_statistic_raw(self, uid: str) -> List[Statistics]:
        # TODO: cache?
        return self.statistics_resource.get_list_raw(uid=uid)

    def get_statistic(self, uid: str) -> List[Dict]:
        # TODO: cache?
        return self.statistics_resource.get_list(uid=uid)
