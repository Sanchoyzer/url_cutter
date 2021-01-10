from datetime import date, datetime
from time import sleep
from urllib.parse import urlparse

import pytest

from url_cutter.depends import get_app_settings, get_cache_db, get_main_db_
from url_cutter.entities.cutter.service import CutterService
from url_cutter.entities.url.schema import UrlCreateRequest
from url_cutter.exceptions import UidAlreadyInUse, UrlAlreadyShort, UrlNotAvailable


@pytest.fixture(scope='session')
def s_cutter():
    with get_main_db_() as main_db:
        yield CutterService(main_db=main_db, cache_db=get_cache_db(), settings=get_app_settings())


def test_create_simple(s_cutter, faker, headers, client, mock_check_url):
    short_url, expiry_at = s_cutter.create(obj_in=UrlCreateRequest(url=(url := faker.url())))
    assert short_url and expiry_at and expiry_at > datetime.utcnow()
    mock_check_url.assert_called_once()

    uid = urlparse(short_url).path.split('/')[-1]
    assert s_cutter.get(uid=uid, headers=headers, client=client) == url


def test_create_with_custom_uid(s_cutter, faker, headers, client, mock_check_url):
    url, custom_uid = faker.url(), faker.pystr()
    short_url, expiry_at = s_cutter.create(obj_in=UrlCreateRequest(url=url, custom_uid=custom_uid))
    assert short_url and expiry_at and expiry_at > datetime.utcnow()
    assert urlparse(short_url).path.split('/')[-1] == custom_uid
    mock_check_url.assert_called_once()

    assert s_cutter.get(uid=custom_uid, headers=headers, client=client) == url


def test_create_with_same_url(s_cutter, source_url, headers, client, mock_check_url, mock_warning):
    short_url, expiry_at = s_cutter.create(obj_in=UrlCreateRequest(url=source_url.link))
    assert short_url and expiry_at and (uid2 := urlparse(short_url).path.split('/')[-1])
    mock_check_url.assert_called_once()

    assert source_url.uid != uid2
    assert source_url.link == s_cutter.get(uid=source_url.uid, headers=headers, client=client)
    assert source_url.link == s_cutter.get(uid=uid2, headers=headers, client=client)
    mock_warning.assert_called_once()


def test_create_with_same_uid(s_cutter, source_url, mock_check_url):
    with pytest.raises(UidAlreadyInUse):
        s_cutter.create(obj_in=UrlCreateRequest(url=source_url.link, custom_uid=source_url.uid))
    mock_check_url.assert_called_once()


def test_create_unavailable_url(s_cutter, faker, mock_check_url_fail):
    with pytest.raises(UrlNotAvailable):
        s_cutter.create(obj_in=UrlCreateRequest(url=faker.url()))
    mock_check_url_fail.assert_called_once()


def test_create_already_short(s_cutter, faker, mock_check_url):
    short_url, _ = s_cutter.create(obj_in=UrlCreateRequest(url=faker.url()))
    mock_check_url.assert_called_once()

    with pytest.raises(UrlAlreadyShort):
        s_cutter.create(obj_in=UrlCreateRequest(url=short_url))


def test_get_expiry_url(s_cutter, faker, headers, client, mock_check_url):
    short_url, expiry_at = s_cutter.create(obj_in=UrlCreateRequest(url=(url := faker.url())))
    assert short_url and expiry_at and (uid := urlparse(short_url).path.split('/')[-1])
    mock_check_url.assert_called_once()

    assert s_cutter.get(uid=uid, headers=headers, client=client) == url
    sleep((expiry_at - datetime.utcnow()).total_seconds() + 0.5)
    assert s_cutter.get(uid=uid, headers=headers, client=client) is None


def test_get_non_existing_url(s_cutter, faker, headers, client):
    assert s_cutter.get(uid=faker.pystr(), headers=headers, client=client) is None


def test_get_expiry_statistics_raw(s_cutter, faker, client, request_headers, mock_check_url):
    short_url, expiry_at = s_cutter.create(obj_in=UrlCreateRequest(url=(url := faker.url())))
    assert short_url and expiry_at and (uid := urlparse(short_url).path.split('/')[-1])
    mock_check_url.assert_called_once()

    assert s_cutter.get(uid=uid, headers=request_headers, client=client) == url
    assert s_cutter.get_statistic_raw(uid=uid)

    sleep((expiry_at - datetime.utcnow()).total_seconds() + 0.5)
    assert s_cutter.get(uid=uid, headers=request_headers, client=client) is None
    assert s_cutter.get_statistic_raw(uid=uid) == []


def test_create_with_statistics(s_cutter, faker, source_url, headers, client, mock_warning):
    today = datetime.combine(date.today(), datetime.min.time())
    for i in range(faker.pyint(min_value=3, max_value=9)):
        assert s_cutter.get(uid=source_url.uid, headers=headers, client=client) == source_url.link
        stat = s_cutter.get_statistic(uid=source_url.uid)
        assert len(stat) == 1 and stat[0] == {'click_count': i + 1, 'create_date': today}
    mock_warning.assert_called_once()


def test_create_simple_with_statistics_fail(s_cutter, faker):
    assert s_cutter.get_statistic_raw(uid=faker.pystr()) == []
