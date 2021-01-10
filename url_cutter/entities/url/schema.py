from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, HttpUrl, conint, constr


class BaseSchema(BaseModel):
    pass


class BaseDBSchema(BaseSchema):
    class Config:
        orm_mode = True


class UrlCreateRequest(BaseSchema):
    url: HttpUrl
    custom_uid: Optional[constr(strip_whitespace=True, min_length=2)]
    qr: bool = False


class UrlCreateResponse(BaseDBSchema):
    short_url: HttpUrl


class StatisticRawItemResponse(BaseDBSchema):
    created_at: datetime
    user_agent: constr(min_length=1)
    host: constr(min_length=1)


class StatisticRawResponse(BaseSchema):
    items: List[StatisticRawItemResponse]


class StatisticItemResponse(BaseSchema):
    create_date: datetime
    click_count: conint(ge=0)


class StatisticResponse(BaseSchema):
    items: List[StatisticItemResponse]
