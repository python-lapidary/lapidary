import httpx

from lapidary.runtime import ClientBase


class ClientTestBase(ClientBase):
    def __init__(self, client: httpx.AsyncClient | None = None):
        super().__init__(client=client)
