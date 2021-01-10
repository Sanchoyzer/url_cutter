from functools import wraps
from io import BytesIO
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse, RedirectResponse, Response, StreamingResponse
from fastapi_utils.cbv import cbv
from sqlalchemy.orm import Session

from url_cutter.cache import Cache
from url_cutter.depends import check_api_key, get_app_settings, get_cache_db, get_main_db
from url_cutter.entities.cutter.service import CutterService
from url_cutter.entities.statistics.model import Statistics
from url_cutter.entities.url.schema import (
    StatisticRawResponse,
    StatisticResponse,
    UrlCreateRequest,
    UrlCreateResponse,
)
from url_cutter.settings import AppSettings


router = APIRouter()


def obj_or_404(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if result := func(*args, **kwargs):
            return result
        else:
            return Response(status_code=status.HTTP_404_NOT_FOUND)

    return inner


def wrap_items(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if isinstance(result := func(*args, **kwargs), Response):
            return result
        else:
            return {'items': result}

    return inner


def _get_cutter_service(
    main_db: Session = Depends(get_main_db),
    cache_db: Cache = Depends(get_cache_db),
    settings: AppSettings = Depends(get_app_settings),
) -> CutterService:
    return CutterService(main_db=main_db, cache_db=cache_db, settings=settings)


@cbv(router)
class UrlView:
    service: CutterService = Depends(_get_cutter_service)
    settings: AppSettings = Depends(get_app_settings)

    @router.post('/', dependencies=[Depends(check_api_key)])
    def create_url(self, obj_in: UrlCreateRequest) -> Response:
        if obj_in.qr:
            qr, expiry_at = self.service.create_qr_code(obj_in=obj_in)
            qr.save(img_stream := BytesIO())
            img_stream.seek(0)
            headers = {'X-Expiry-At': expiry_at.isoformat()}
            return StreamingResponse(img_stream, media_type='image/png', headers=headers)
        else:
            short_url, expiry_at = self.service.create(obj_in=obj_in)
            headers = {'X-Expiry-At': expiry_at.isoformat()}
            content = UrlCreateResponse(**{'short_url': short_url}).dict()
            return JSONResponse(content, headers=headers)

    @router.get('/{uid}')
    @obj_or_404
    def get_url(self, uid: str, r: Request) -> Optional[RedirectResponse]:
        if url := self.service.get(uid=uid, headers=r.headers.items(), client=r.client._asdict()):
            return RedirectResponse(url=url)
        return None

    @router.get(
        '/{uid}/statistics_raw',
        response_model=StatisticRawResponse,
        dependencies=[Depends(check_api_key)],
    )
    @wrap_items
    def get_statistic_raw(self, uid: str) -> List[Statistics]:
        return self.service.get_statistic_raw(uid=uid)

    @router.get(
        '/{uid}/statistics', response_model=StatisticResponse, dependencies=[Depends(check_api_key)]
    )
    @wrap_items
    def get_statistic(self, uid: str) -> List[Dict]:
        return self.service.get_statistic(uid=uid)
