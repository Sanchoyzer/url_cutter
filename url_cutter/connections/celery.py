from celery import Celery

from url_cutter.settings import get_settings


settings = get_settings()

celery = Celery(
    'tasks',
    broker=settings.CELERY_BROKER,
    backend=settings.CELERY_BACKEND,
    include=['url_cutter.tasks.background'],
)

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    task_always_eager=settings.CELERY_ALWAYS_EAGER,
)

celery.conf.beat_schedule = {
    'clear-expired-urls': {
        'task': 'url_cutter.tasks.background.clear_expired_urls',
        'schedule': settings.PERIOD_CLEARING_EXPIRED_URLS_SEC,
    },
    'clear-expired-api-keys': {
        'task': 'url_cutter.tasks.background.clear_expired_api_keys',
        'schedule': settings.PERIOD_CLEARING_EXPIRED_API_KEYS_SEC,
    },
}
