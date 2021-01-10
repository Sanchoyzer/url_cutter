from fastapi import FastAPI
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from url_cutter import __version__
from url_cutter.connections import init_sentry
from url_cutter.entities.cutter.view import router as router_v1_urls
from url_cutter.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title='url_cutter', version=__version__)

    if sentry_dsn := settings.SENTRY_DSN:
        init_sentry(sentry_dsn=sentry_dsn)
        app.add_middleware(middleware_class=SentryAsgiMiddleware)

    app.include_router(router=router_v1_urls, prefix='/v1/urls')

    return app
