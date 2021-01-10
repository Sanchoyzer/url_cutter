from datetime import date, datetime
from io import BytesIO
from time import sleep
from urllib.parse import urlparse

import pytest
from fastapi import status
from qrcode import make as make_qr


@pytest.fixture(scope='session')
def path_():
    return '/v1/urls/'


@pytest.fixture(scope='session')
def path_stat():
    return '/v1/urls/{uid}/statistics'


@pytest.fixture(scope='session')
def path_stat_raw():
    return '/v1/urls/{uid}/statistics_raw'


def test_create_simple(web_client, faker, path_, headers, mock_check_url):
    r = web_client.post(path_, json={'url': (url := faker.url())}, headers=headers)
    assert r.status_code == status.HTTP_200_OK, r.text
    assert (r_json := r.json()) and (short_url := r_json['short_url'])
    assert datetime.fromisoformat(r.headers['X-Expiry-At']) > datetime.utcnow()
    mock_check_url.assert_called_once()

    r = web_client.get(short_url, allow_redirects=False, headers=headers)
    assert r.status_code == status.HTTP_307_TEMPORARY_REDIRECT, r.text
    assert r.headers['location'] == url


def test_create_with_custom_uid(web_client, faker, path_, headers, mock_check_url):
    url, custom_uid = faker.url(), faker.pystr(min_chars=6, max_chars=6)
    r = web_client.post(path_, json={'url': url, 'custom_uid': custom_uid}, headers=headers)
    assert r.status_code == status.HTTP_200_OK, r.text
    assert (r_json := r.json()) and (short_url := r_json['short_url'])
    assert short_url.endswith(f'/{custom_uid}')
    assert datetime.fromisoformat(r.headers['X-Expiry-At']) > datetime.utcnow()
    mock_check_url.assert_called_once()

    r = web_client.get(short_url, allow_redirects=False, headers=headers)
    assert r.status_code == status.HTTP_307_TEMPORARY_REDIRECT, r.text
    assert r.headers['location'] == url


@pytest.mark.parametrize('custom_uid', ['qw=er', 'a sdf', '?qw=12&er=34', 'a_b', 'тест'])
def test_create_with_custom_uid_fail(web_client, faker, path_, custom_uid, headers):
    r = web_client.post(path_, json={'url': faker.url(), 'custom_uid': custom_uid}, headers=headers)
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, r.text


def test_create_with_same_url(
    web_client, path_, source_url, short_url, headers, mock_check_url, mock_warning
):
    r = web_client.post(path_, json={'url': source_url.link}, headers=headers)
    assert r.status_code == status.HTTP_200_OK, r.text
    assert (r_json := r.json()) and (short_url_2 := r_json.get('short_url'))
    mock_check_url.assert_called_once()

    assert short_url != short_url_2
    r_1 = web_client.get(short_url, allow_redirects=False, headers=headers)
    r_2 = web_client.get(short_url_2, allow_redirects=False, headers=headers)
    assert r_1.status_code == r_2.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert r_1.headers['location'] == r_2.headers['location']
    mock_warning.assert_called_once()


def test_create_with_same_uid(web_client, faker, path_, source_url, headers, mock_check_url):
    r = web_client.post(path_, json={'url': faker.url(), 'custom_uid': source_url.uid}, headers=headers)
    assert r.status_code == status.HTTP_400_BAD_REQUEST, r.text
    mock_check_url.assert_called_once()


def test_create_unavailable_url(web_client, path_, faker, headers, mock_check_url_fail):
    r = web_client.post(path_, json={'url': faker.url()}, headers=headers)
    assert r.status_code == status.HTTP_400_BAD_REQUEST, r.text
    mock_check_url_fail.assert_called_once()


def test_create_qr_code(web_client, path_, faker, headers, mock_check_url, settings):
    url, custom_uid = faker.url(), faker.pystr(min_chars=6, max_chars=6)
    r = web_client.post(path_, json={'url': url, 'custom_uid': custom_uid, 'qr': True}, headers=headers)
    assert r.status_code == status.HTTP_200_OK, r.text
    assert datetime.fromisoformat(r.headers['X-Expiry-At']) > datetime.utcnow()
    mock_check_url.assert_called_once()

    qr = make_qr(data=f'{settings.STORAGE_URL}{custom_uid}')
    qr.save(img_stream := BytesIO())
    img_stream.seek(0)
    assert r.content and r.content == img_stream.read()


def test_create_already_short(web_client, path_, short_url, headers):
    r = web_client.post(path_, json={'url': short_url}, headers=headers)
    assert r.status_code == status.HTTP_400_BAD_REQUEST, r.text


def test_get_expiry_url(web_client, faker, path_, headers, mock_check_url):
    r = web_client.post(path_, json={'url': faker.url()}, headers=headers)
    assert r.status_code == status.HTTP_200_OK and (r_json := r.json()), r.text
    mock_check_url.assert_called_once()
    expiry_at = r.headers['X-Expiry-At']

    path_get = urlparse(short_url := r_json['short_url']).path
    r = web_client.get(path_get, allow_redirects=False, headers=headers)
    assert r.status_code == status.HTTP_307_TEMPORARY_REDIRECT, r.text

    sleep((datetime.fromisoformat(expiry_at) - datetime.utcnow()).total_seconds() + 0.5)

    r = web_client.get(short_url, allow_redirects=False, headers=headers)
    assert r.status_code == status.HTTP_404_NOT_FOUND, r.text


def test_get_non_existing_url(web_client, faker, path_, headers):
    r = web_client.get(f'{path_}{faker.pystr()}', allow_redirects=False, headers=headers)
    assert r.status_code == status.HTTP_404_NOT_FOUND, r.text


def test_create_with_statistics_raw(
    web_client, faker, path_stat_raw, source_url, short_url, headers, mock_warning
):
    for i in range(faker.pyint(min_value=3, max_value=9)):
        r = web_client.get(path_stat_raw.format(uid=source_url.uid), headers=headers)
        assert r.status_code == status.HTTP_200_OK, r.text
        assert (r_json := r.json()) and len(items := r_json.get('items')) == i
        if i > 0:
            assert {j['host'] for j in items} == {web_client.headers['user-agent']}
            assert {j['user_agent'] for j in items} == {headers['User-Agent']}

        r = web_client.get(short_url, allow_redirects=False, headers=headers)
        assert r.status_code == status.HTTP_307_TEMPORARY_REDIRECT, r.text
    mock_warning.assert_called_once()


def test_create_simple_with_statistics_raw_fail(web_client, faker, path_stat_raw, headers):
    r = web_client.get(path_stat_raw.format(uid=faker.pystr()), headers=headers)
    assert r.status_code == status.HTTP_200_OK and r.json().get('items') == [], r.text


def test_get_expiry_statistics_raw(web_client, faker, path_, path_stat_raw, headers, mock_check_url):
    r = web_client.post(path_, json={'url': faker.url()}, headers=headers)
    assert r.status_code == status.HTTP_200_OK and (r_json := r.json()), r.text
    assert (short_url := r_json['short_url'])
    mock_check_url.assert_called_once()

    uid = urlparse(short_url).path.split('/')[-1]
    expiry_at = r.headers['X-Expiry-At']

    r = web_client.get(short_url, allow_redirects=False, headers=headers)
    assert r.status_code == status.HTTP_307_TEMPORARY_REDIRECT, r.text

    r = web_client.get(path_stat_raw.format(uid=uid), headers=headers)
    assert r.status_code == status.HTTP_200_OK and r.json()['items'], r.text

    delay = int((datetime.fromisoformat(expiry_at) - datetime.utcnow()).total_seconds()) + 1
    sleep(delay)

    r = web_client.get(short_url, allow_redirects=False, headers=headers)
    assert r.status_code == status.HTTP_404_NOT_FOUND, r.text

    r = web_client.get(path_stat_raw.format(uid=uid), headers=headers)
    assert r.status_code == status.HTTP_200_OK and r.json().get('items') == [], r.text


def test_create_with_statistics(
    web_client, faker, path_stat, source_url, short_url, headers, mock_warning
):
    today = date.today().strftime('%Y-%m-%d')
    for i in range(faker.pyint(min_value=3, max_value=9)):
        r = web_client.get(short_url, allow_redirects=False, headers=headers)
        assert r.status_code == status.HTTP_307_TEMPORARY_REDIRECT, r.text

        r = web_client.get(path_stat.format(uid=source_url.uid), headers=headers)
        assert r.status_code == status.HTTP_200_OK, r.text
        assert (r_json := r.json()) and (items := r_json.get('items')) and len(items) == 1
        assert items[0] == {'click_count': i + 1, 'create_date': today}
    mock_warning.assert_called_once()


def test_create_simple_with_statistics_fail(web_client, faker, path_stat, headers):
    r = web_client.get(path_stat.format(uid=faker.pystr()), headers=headers)
    assert r.status_code == status.HTTP_200_OK and r.json().get('items') == [], r.text


def test_api_key_fail(web_client, faker, path_, mock_check_url):
    r = web_client.post(path_, json={'url': (url := faker.url())})
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, r.text

    r = web_client.post(path_, json={'url': url}, headers={'Authorization': f'ApiKey {faker.pystr()}'})
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, r.text

    non_exists_key = f'ApiKey {faker.pystr(min_chars=32, max_chars=32)}'
    r = web_client.post(path_, json={'url': url}, headers={'Authorization': non_exists_key})
    assert r.status_code == status.HTTP_401_UNAUTHORIZED, r.text
    mock_check_url.assert_not_called()


def test_api_key_fail_2(
    web_client, path_stat, path_stat_raw, source_url, short_url, mock_check_url, mock_warning
):
    r = web_client.get(short_url, allow_redirects=False)
    assert r.status_code == status.HTTP_307_TEMPORARY_REDIRECT, r.text
    mock_warning.assert_called_once()

    r = web_client.get(path_stat.format(uid=source_url.uid))
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, r.text

    r = web_client.get(path_stat_raw.format(uid=source_url.uid))
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, r.text
    mock_check_url.assert_not_called()


def test_api_key_expire(web_client, faker, path_, headers, api_key, mock_check_url):
    r = web_client.post(path_, json={'url': faker.url()}, headers=headers)
    assert r.status_code == status.HTTP_200_OK, r.text
    mock_check_url.assert_called_once()

    sleep((api_key.expiry_at - datetime.utcnow()).total_seconds() + 0.5)

    r = web_client.post(path_, json={'url': faker.url()}, headers=headers)
    assert r.status_code == status.HTTP_401_UNAUTHORIZED, r.text


def test_miss_cache(web_client, source_url, short_url, headers, mock_warning):
    r = web_client.get(short_url, allow_redirects=False, headers=headers)
    assert r.status_code == status.HTTP_307_TEMPORARY_REDIRECT, r.text
    assert r.headers['location'] == source_url.link
    mock_warning.assert_called_once()
