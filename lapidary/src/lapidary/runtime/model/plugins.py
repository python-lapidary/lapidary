import abc
from typing import Generic, TypeVar, Generator

import httpx

T_original = TypeVar('T_original')
T_paged = TypeVar('T_paged')


class PagingPlugin(abc.ABC, Generic[T_original, T_paged]):
    @abc.abstractmethod
    def page_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        raise NotImplementedError

    def map_response(self, response_body: T_original) -> T_paged:
        return response_body
