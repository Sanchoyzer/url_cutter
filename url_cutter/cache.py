from datetime import datetime
from typing import List, Optional, Union

from url_cutter.connections import Redis, RedisConnection


class Cache:
    __slots__ = ('_redis',)

    RedisValueType = Union[int, float, datetime, str]

    SEPARATOR = ':'

    def __init__(self) -> None:
        super().__init__()
        self._redis: Redis = RedisConnection

    def _get_full_key(self, prefix: str, key: str) -> str:
        return f'{prefix}{self.SEPARATOR}{key}'

    def add(self, prefix: str, key: str, value: RedisValueType, ex: Optional[int] = None) -> bool:
        if isinstance(value, datetime):
            value = value.isoformat()
        return self._redis.set(name=self._get_full_key(prefix=prefix, key=key), value=value, ex=ex)

    def get(self, prefix: str, key: str) -> Optional[str]:
        if value := self._redis.get(name=self._get_full_key(prefix=prefix, key=key)):
            return value.decode('utf-8')
        return None

    def mget(self, prefix: str, keys: List[str]) -> List[Optional[str]]:
        return self._redis.mget(*[self._get_full_key(prefix=prefix, key=k) for k in keys])

    def echo(self, value: RedisValueType) -> str:
        return self._redis.echo(value)

    def flushall(self, asynchronous: bool = False):
        return self._redis.flushall(asynchronous=asynchronous)


CacheSession = Cache()
