import httpx

from lapidary.runtime import ClientBase


class ClientTestBase(ClientBase):
    def __init__(self, client: httpx.AsyncClient):
        super().__init__(base_url='http://example.com', _http_client=client)
