from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from qrcode import QRCode
from qrcode.image.pil import PilImage
from redis import Redis
from requests.exceptions import ConnectionError
from sqlalchemy.orm import Session

from url_cutter.background_tasks import update_statistics
from url_cutter.entities.statistics.model import Statistics
from url_cutter.entities.statistics.resource import StatisticsResource
from url_cutter.entities.url.model import Url
from url_cutter.entities.url.resource import UrlResource
from url_cutter.entities.url.schema import UrlCreateRequest
from url_cutter.exceptions import UrlAlreadyShort, UrlNotAvailable
from url_cutter.settings import AppSettings


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
    )

    def __init__(self, main_db: Session, cache_db: Redis, settings: AppSettings) -> None:
        self.main_db = main_db
        self.cache_db = cache_db
        self.url_resource = UrlResource(main_db=main_db)
        self.statistics_resource = StatisticsResource(main_db=main_db)
        self.url_prefix = settings.STORAGE_URL
        self.uid_len = settings.UID_LEN
        self.url_ttl = settings.URL_TTL_SEC

    # TODO: to celery?
    def _add_to_cache(self, db_obj: Url, ex: int) -> None:
        self.cache_db.set(name=db_obj.uid, value=db_obj.link, ex=ex)

    def create(self, obj_in: UrlCreateRequest) -> Tuple[str, datetime]:
        if urlparse(obj_in.url).netloc == urlparse(self.url_prefix).netloc:
            raise UrlAlreadyShort('url already short')

        try:
            requests.head(url=obj_in.url, timeout=1)
        except ConnectionError:
            raise UrlNotAvailable(f'url "{obj_in.url}" is not available')

        url = self.url_resource.create(obj_in=obj_in, uid_len=self.uid_len, ttl=self.url_ttl)
        self._add_to_cache(db_obj=url, ex=self.url_ttl)
        return self.url_prefix + url.uid, url.expiry_at

    def create_qr_code(self, obj_in: UrlCreateRequest) -> Tuple[PilImage, datetime]:
        short_url, expiry_at = self.create(obj_in=obj_in)
        qr = QRCode(version=1)
        qr.add_data(data=short_url)
        qr.make(fit=True)
        return qr.make_image(), expiry_at

    def get(self, uid: str, headers: List[Tuple[str, str]], client: Dict) -> Optional[str]:
        if cache_url := self.cache_db.get(uid):
            update_statistics.delay(url_uid=uid, headers=headers, client=client)
            return cache_url.decode('utf-8')

        if not (url := self.url_resource.get(uid=uid)):
            return None

        # TODO: warning?
        if url.expiry_at > datetime.utcnow():
            self._add_to_cache(db_obj=url, ex=url.expiry_at - url.created_at)
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
