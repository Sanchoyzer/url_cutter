### Описание

Api для сервиса сокращения урлов. Сокращает, генерирует qr код, считает статистику.

Основная БД -- postgresql (+sqlalchemy), кэш -- redis, celery для фоновых задач, alembic для миграций.


### Требования

 - Python 3.8
 - docker
 - docker-compose
 - poetry


### Пример `.env`

```
MAIN_DB_URI='postgres://user:pass@pg:5432/my_db'
CACHE_DB_URI='redis://user:pass@redis:6379/0'
STORAGE_URL='https://url-cutter.com/v1/urls/'
UID_LEN=4
CELERY_BROKER=redis://user:pass@redis:6379/1
CELERY_BACKEND=redis://user:pass@redis:6379/2
URL_TTL_SEC=3600
PERIOD_CLEARING_EXPIRED_URLS_SEC=600
API_KEY_TTL_SEC=86400
PERIOD_CLEARING_EXPIRED_API_KEYS_SEC=600
SENTRY_DSN=https://key@sentry.io/proj_id
```


### Документация (автогенерация)

 - `/docs` (Swagger UI)

 - `/redoc` (ReDoc)


### Локальная отладка

Postgres
```
docker run --rm --name pg -p 5432:5432 -e POSTGRES_HOST_AUTH_METHOD=trust postgres:13-alpine
```

Redis
```
docker run --rm --name redis -p 6379:6379 redis:6-alpine
```

Celery
```
celery -A url_cutter.connections.celery worker --loglevel=info
celery -A url_cutter.connections.celery beat --loglevel=info
```

Сервис
```
uvicorn url_cutter.main:app --reload --host '0.0.0.0' --port 9000
```

Тесты
```
pytest
```


### Локальные миграции

**NB**: `ModuleNotFoundError: No module named 'url_cutter'` -> `export PYTHONPATH=$PWD`

Накатить существующие миграции
```
alembic upgrade head
```

Сгенерировать новую миграцию
```
alembic revision --autogenerate -m "caption"
```


### Poetry

Обновить/создать `poetry.lock`
```
poetry install --no-root
```

Получить requirements.txt
```
poetry export --output requirements.txt --dev --without-hashes
```


### Запуск сервиса

```
./dc.sh up -d
```


### Бекап

Создание
```
./dc.sh exec pg pg_dump -F c -C -U postgres -d postgres -f /home/backup.pgdmp
```

Восстановление
```
./dc.sh exec pg pg_restore -C -U postgres -d postgres /home/backup.pgdmp
```