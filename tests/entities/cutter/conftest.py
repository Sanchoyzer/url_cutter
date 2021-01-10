from unittest.mock import Mock, patch

import pytest
from fastapi import status
from requests.exceptions import ConnectionError


@pytest.fixture()
def mock_check_url():
    mock_resp = Mock(status_code=status.HTTP_200_OK)
    with patch('url_cutter.entities.cutter.service.requests.head', return_value=mock_resp) as mock:
        yield mock


@pytest.fixture()
def mock_check_url_fail():
    with patch(
        'url_cutter.entities.cutter.service.requests.head', side_effect=ConnectionError()
    ) as mock:
        yield mock
