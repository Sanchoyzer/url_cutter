from datetime import datetime
from time import sleep
from urllib.parse import urlparse

import pytest
from fastapi import status


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

    r = web_client.get(urlparse(short_url).path, allow_redirects=False, headers=headers)
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

    r = web_client.get(urlparse(short_url).path, allow_redirects=False, headers=headers)
    assert r.status_code == status.HTTP_307_TEMPORARY_REDIRECT, r.text
    assert r.headers['location'] == url


def test_create_with_same_url(web_client, faker, path_, headers, mock_check_url):
    r = web_client.post(path_, json={'url': (url := faker.url())}, headers=headers)
    assert r.status_code == status.HTTP_200_OK, r.text
    assert (r_json := r.json()) and (short_url_1 := r_json.get('short_url'))
    assert mock_check_url.call_count == 1

    r = web_client.post(path_, json={'url': url}, headers=headers)
    assert r.status_code == status.HTTP_200_OK, r.text
    assert (r_json := r.json()) and (short_url_2 := r_json.get('short_url'))
    assert mock_check_url.call_count == 2

    assert short_url_1 != short_url_2
    r_1 = web_client.get(urlparse(short_url_1).path, allow_redirects=False, headers=headers)
    r_2 = web_client.get(urlparse(short_url_2).path, allow_redirects=False, headers=headers)
    assert r_1.headers['location'] == r_2.headers['location']


def test_create_with_same_uid(web_client, faker, path_, headers, mock_check_url):
    r = web_client.post(path_, json={'url': faker.url()}, headers=headers)
    assert r.status_code == status.HTTP_200_OK, r.text
    assert (r_json := r.json()) and (short_url := r_json.get('short_url'))
    assert mock_check_url.call_count == 1

    custom_uid = urlparse(short_url).path.split('/')[-1]
    r = web_client.post(path_, json={'url': faker.url(), 'custom_uid': custom_uid}, headers=headers)
    assert r.status_code == status.HTTP_400_BAD_REQUEST, r.text
    assert mock_check_url.call_count == 2


def test_create_unavailable_url(web_client, path_, faker, headers, mock_check_url_fail):
    r = web_client.post(path_, json={'url': faker.url()}, headers=headers)
    assert r.status_code == status.HTTP_400_BAD_REQUEST, r.text
    mock_check_url_fail.assert_called_once()


def test_create_qr_code(web_client, path_, faker, headers, mock_check_url):
    # TODO: delete hardcode & check a picture
    r = web_client.post(path_, json={'url': faker.url(), 'qr': True}, headers=headers)
    assert r.status_code == status.HTTP_200_OK, r.text
    assert datetime.fromisoformat(r.headers['X-Expiry-At']) > datetime.utcnow()
    assert r.content and len(r.content) > 500
    mock_check_url.assert_called_once()


def test_create_already_short(web_client, path_, faker, headers, mock_check_url):
    r = web_client.post(path_, json={'url': faker.url()}, headers=headers)
    assert r.status_code == status.HTTP_200_OK, r.text
    assert (r_json := r.json()) and (short_url := r_json.get('short_url'))
    mock_check_url.assert_called_once()

    r = web_client.post(path_, json={'url': short_url}, headers=headers)
    assert r.status_code == status.HTTP_400_BAD_REQUEST, r.text


def test_get_expiry_url(web_client, faker, path_, headers, mock_check_url):
    r = web_client.post(path_, json={'url': faker.url()}, headers=headers)
    assert r.status_code == status.HTTP_200_OK and (r_json := r.json()), r.text
    expiry_at = r.headers['X-Expiry-At']

    path_get = urlparse(short_url := r_json['short_url']).path
    r = web_client.get(path_get, allow_redirects=False, headers=headers)
    assert r.status_code == status.HTTP_307_TEMPORARY_REDIRECT, r.text

    sleep((datetime.fromisoformat(expiry_at) - datetime.utcnow()).total_seconds() + 0.5)

    r = web_client.get(urlparse(short_url).path, allow_redirects=False, headers=headers)
    assert r.status_code == status.HTTP_404_NOT_FOUND, r.text


def test_get_unexisting_url(web_client, faker, path_, headers, mock_check_url):
    r = web_client.get(f'{path_}{faker.pystr()}', allow_redirects=False, headers=headers)
    assert r.status_code == status.HTTP_404_NOT_FOUND, r.text


def test_create_with_statistics_raw(web_client, faker, path_, path_stat_raw, headers, mock_check_url):
    r = web_client.post(path_, json={'url': faker.url()}, headers=headers)
    assert r.status_code == status.HTTP_200_OK, r.text
    assert (short_url := r.json()['short_url'])
    uid = urlparse(short_url).path.split('/')[-1]

    for i in range(faker.pyint(min_value=3, max_value=9)):
        r = web_client.get(path_stat_raw.format(uid=uid), headers=headers)
        assert r.status_code == status.HTTP_200_OK, r.text
        assert (r_json := r.json()) and len(items := r_json.get('items')) == i
        if i > 0:
            assert {j['host'] for j in items} == {web_client.headers['user-agent']}
            assert {j['user_agent'] for j in items} == {headers['User-Agent']}

        r = web_client.get(urlparse(short_url).path, allow_redirects=False, headers=headers)
        assert r.status_code == status.HTTP_307_TEMPORARY_REDIRECT, r.text


def test_create_simple_with_statistics_raw_fail(web_client, faker, path_stat_raw, headers):
    r = web_client.get(path_stat_raw.format(uid=faker.pystr()), headers=headers)
    assert r.status_code == status.HTTP_200_OK and r.json().get('items') == [], r.text


def test_get_expiry_statistics_raw(web_client, faker, path_, path_stat_raw, headers, mock_check_url):
    r = web_client.post(path_, json={'url': faker.url()}, headers=headers)
    assert r.status_code == status.HTTP_200_OK and (r_json := r.json()), r.text
    assert (short_url := r_json['short_url'])

    uid = urlparse(short_url).path.split('/')[-1]
    expiry_at = r.headers['X-Expiry-At']

    r = web_client.get(urlparse(short_url).path, allow_redirects=False, headers=headers)
    assert r.status_code == status.HTTP_307_TEMPORARY_REDIRECT, r.text

    r = web_client.get(path_stat_raw.format(uid=uid), headers=headers)
    assert r.status_code == status.HTTP_200_OK and r.json()['items'], r.text

    delay = int((datetime.fromisoformat(expiry_at) - datetime.utcnow()).total_seconds()) + 1
    sleep(delay)

    r = web_client.get(urlparse(short_url).path, allow_redirects=False, headers=headers)
    assert r.status_code == status.HTTP_404_NOT_FOUND, r.text

    r = web_client.get(path_stat_raw.format(uid=uid), headers=headers)
    assert r.status_code == status.HTTP_200_OK and r.json().get('items') == [], r.text


def test_create_with_statistics(web_client, faker, path_, path_stat, headers, mock_check_url):
    r = web_client.post(path_, json={'url': faker.url()}, headers=headers)
    assert r.status_code == status.HTTP_200_OK, r.text
    assert (short_url := r.json()['short_url'])

    uid = urlparse(short_url).path.split('/')[-1]
    today = datetime.utcnow().strftime('%Y-%m-%dT00:00:00')

    for i in range(faker.pyint(min_value=3, max_value=9)):
        r = web_client.get(urlparse(short_url).path, allow_redirects=False, headers=headers)
        assert r.status_code == status.HTTP_307_TEMPORARY_REDIRECT, r.text

        r = web_client.get(path_stat.format(uid=uid), headers=headers)
        assert r.status_code == status.HTTP_200_OK, r.text
        assert (r_json := r.json()) and (items := r_json.get('items')) and len(items) == 1
        assert items[0] == {'click_count': i + 1, 'create_date': today}


def test_api_key_fail(web_client, faker, path_, mock_check_url):
    r = web_client.post(path_, json={'url': (url := faker.url())})
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, r.text

    r = web_client.post(path_, json={'url': url}, headers={'Authorization': f'ApiKey {faker.pystr()}'})
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, r.text

    r = web_client.post(
        path_,
        json={'url': url},
        headers={'Authorization': f'ApiKey {faker.pystr(min_chars=32, max_chars=32)}'},
    )
    assert r.status_code == status.HTTP_401_UNAUTHORIZED, r.text


def test_api_key_fail_2(web_client, faker, path_, path_stat, path_stat_raw, headers, mock_check_url):
    r = web_client.post(path_, json={'url': faker.url()}, headers=headers)
    assert r.status_code == status.HTTP_200_OK, r.text

    short_url = r.json()['short_url']
    get_url = urlparse(short_url).path

    r = web_client.get(get_url, allow_redirects=False)
    assert r.status_code == status.HTTP_307_TEMPORARY_REDIRECT, r.text

    r = web_client.get(path_stat.format(uid=(uid := get_url.split('/')[-1])))
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, r.text

    r = web_client.get(path_stat_raw.format(uid=uid))
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, r.text


def test_api_key_expire(web_client, faker, path_, headers, api_key, mock_check_url):
    r = web_client.post(path_, json={'url': faker.url()}, headers=headers)
    assert r.status_code == status.HTTP_200_OK, r.text

    sleep((api_key.expiry_at - datetime.utcnow()).total_seconds() + 0.5)

    r = web_client.post(path_, json={'url': faker.url()}, headers=headers)
    assert r.status_code == status.HTTP_401_UNAUTHORIZED, r.text
