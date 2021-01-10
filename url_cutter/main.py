import sentry_sdk
from fastapi import status
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from url_cutter.app import create_app
from url_cutter.exceptions import AuthError, ClientError, ServerError
from url_cutter.tasks.startup import warm_up_cache


app = create_app()


@app.on_event('startup')
def startup_event():
    warm_up_cache()


@app.exception_handler(AuthError)
def value_error_exception_handler(request: Request, exc: AuthError):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={'detail': [{'loc': [], 'msg': str(exc), 'type': type(exc).__name__}]},
    )


@app.exception_handler(ClientError)
def value_error_exception_handler(request: Request, exc: ClientError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={'detail': [{'loc': [], 'msg': str(exc), 'type': type(exc).__name__}]},
    )


@app.exception_handler(ServerError)
def value_error_exception_handler(request: Request, exc: ServerError):
    sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={'detail': [{'loc': [], 'msg': str(exc), 'type': type(exc).__name__}]},
    )
