from redis import Redis

from url_cutter.settings import get_settings


settings = get_settings()
RedisConnection: Redis = Redis.from_url(url=settings.CACHE_DB_URI)
