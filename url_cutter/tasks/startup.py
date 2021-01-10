from datetime import datetime

from url_cutter.cache import CacheSession
from url_cutter.depends import get_main_db_
from url_cutter.entities.api_key.model import ApiKey


def warm_up_cache():
    warp_up_api_keys()


def warp_up_api_keys():
    now = datetime.utcnow()
    with get_main_db_() as main_db:
        for item in main_db.query(ApiKey).filter(ApiKey.expiry_at > now).all():
            CacheSession.add(
                prefix='api_key',
                key=item.key,
                value=item.expiry_at,
                ex=item.expiry_at - now,
            )
