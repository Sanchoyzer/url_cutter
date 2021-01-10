# molotov -w 15 -d 5 tests/load_testing/load_test_molotov.py

from time import perf_counter

from fastapi import status
from molotov import events, global_teardown, scenario, setup


_T = {}


@events()
async def record_time(event, **info):
    req = info.get('request')
    if event == 'sending_request':
        _T[req] = perf_counter()
    elif event == 'response_received':
        _T[req] = perf_counter() - _T[req]


@global_teardown()
def display_average():
    print(f'\nAverage response time {sum(_T.values()) / len(_T)} ms')


@setup()
async def init_worker(worker_id, args):
    return {'headers': {'Authorization': 'ApiKey 00000000000000000000000000000000'}}


@scenario(weight=100)
async def test_create(session):
    path_ = 'http://0.0.0.0/v1/urls/'
    url = 'https://ya.ru'
    async with session.post(path_, json={'url': url}) as r:
        assert r.status == status.HTTP_200_OK, r.status
