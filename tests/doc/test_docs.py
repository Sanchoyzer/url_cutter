import pytest
from fastapi import status


@pytest.mark.parametrize(
    'docs_url,openapi_tag',
    [
        ('/openapi.json', None),
        ('/docs', "url: '/openapi.json'"),
        ('/redoc', '<redoc spec-url="/openapi.json">'),
    ],
)
def test_api_get(web_client, docs_url, openapi_tag):
    response = web_client.get(docs_url)
    assert response.status_code == status.HTTP_200_OK, response.text

    if openapi_tag:
        assert openapi_tag in response.text
