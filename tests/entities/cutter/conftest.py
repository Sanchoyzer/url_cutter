from unittest.mock import Mock, patch

import pytest
from fastapi import status
from requests.exceptions import ConnectionError

from tests.entities import factories


@pytest.fixture()
def patch_path():
    return 'url_cutter.entities.cutter.service.requests.head'


@pytest.fixture()
def mock_check_url(patch_path):
    mock_resp = Mock(status_code=status.HTTP_200_OK)
    with patch(patch_path, return_value=mock_resp) as mock:
        yield mock


@pytest.fixture()
def mock_check_url_fail(patch_path):
    with patch(patch_path, side_effect=ConnectionError()) as mock:
        yield mock


@pytest.fixture()
def mock_warning():
    with patch('url_cutter.entities.cutter.service.logging.warning') as mock:
        yield mock


@pytest.fixture()
def source_url():
    return factories.UrlFactory()


@pytest.fixture()
def short_url(source_url, settings):
    return settings.STORAGE_URL + source_url.uid
