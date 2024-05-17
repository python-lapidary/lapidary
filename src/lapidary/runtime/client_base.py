import abc
import logging
from collections.abc import Awaitable, Callable, Iterable, Mapping, MutableMapping
from importlib.metadata import version
from typing import Any, Optional, cast

import httpx
from typing_extensions import Self

from ._httpx import AuthType
from .model.op import OperationModel, get_operation_model
from .model.request import RequestFactory
from .request import build_request
from .types_ import MultiAuth, NamedAuth, SecurityRequirements

logger = logging.getLogger(__name__)

USER_AGENT = f'lapidary.dev/{version("lapidary")}'


class ClientBase(abc.ABC):
    def __init__(
        self,
        base_url: str,
        user_agent: str = USER_AGENT,
        security: Optional[Iterable[SecurityRequirements]] = None,
        _http_client: Optional[httpx.AsyncClient] = None,
        **httpx_kwargs,
    ):
        if httpx_kwargs and _http_client:
            raise TypeError(f'Extra keyword arguments not accepted when passing _http_client: {", ".join(httpx_kwargs.keys())}')

        headers = httpx.Headers(httpx_kwargs.pop('headers', None))
        if user_agent:
            headers['User-Agent'] = user_agent

        self._client = _http_client or httpx.AsyncClient(base_url=base_url, headers=headers, **httpx_kwargs)
        self._security = security
        self._lapidary_operations: MutableMapping[str, OperationModel] = {}
        self._auth: MutableMapping[str, httpx.Auth] = {}
        self._auth_cache: MutableMapping[str, httpx.Auth] = {}

    async def __aenter__(self: Self) -> Self:
        await self._client.__aenter__()
        return self

    async def __aexit__(self, __exc_type=None, __exc_value=None, __traceback=None) -> None:
        await self._client.__aexit__(__exc_type, __exc_value, __traceback)

    async def _request(
        self,
        method: str,
        path: str,
        fn: Callable[..., Awaitable],
        security: Optional[Iterable[SecurityRequirements]],
        actual_params: Mapping[str, Any],
    ):
        if fn.__name__ not in self._lapidary_operations:
            operation = get_operation_model(method, path, fn)
            self._lapidary_operations[fn.__name__] = operation
        else:
            operation = self._lapidary_operations[fn.__name__]

        auth = self._resolve_auth(fn, security)

        request = build_request(
            operation,
            actual_params,
            cast(RequestFactory, self._client.build_request),
        )

        logger.debug('%s %s %s', request.method, request.url, request.headers)

        response = await self._client.send(request, auth=auth)
        await response.aread()

        return operation.handle_response(response)

    def _resolve_auth(self, fn: Callable, security: Optional[Iterable[SecurityRequirements]]) -> AuthType:
        if security:
            sec_name = fn.__name__
            sec_source = security
        elif self._security:
            sec_name = '*'
            sec_source = self._security
        else:
            sec_name = None
            sec_source = None

        if sec_source:
            assert sec_name
            if sec_name not in self._auth_cache:
                auth = self._mk_auth(sec_source)
                self._auth_cache[sec_name] = auth
            else:
                auth = self._auth_cache[sec_name]
            return auth
        else:
            return None

    def lapidary_authenticate(self, *auth_args: NamedAuth, **auth_kwargs: httpx.Auth) -> None:
        """Register named Auth instances for future use with methods that require authentication."""
        if auth_args:
            # make python complain about duplicate names
            self.lapidary_authenticate(**dict(auth_args), **auth_kwargs)

        self._auth.update(auth_kwargs)
        self._auth_cache.clear()

    def lapidary_deauthenticate(self, *sec_names: str) -> None:
        """Remove reference to a given Auth instance.
        Calling with no parameters removes all references"""

        if sec_names:
            for sec_name in sec_names:
                del self._auth[sec_name]
        else:
            self._auth.clear()
        self._auth_cache.clear()

    def _mk_auth(self, security: Iterable[SecurityRequirements]) -> httpx.Auth:
        security = list(security)
        assert security
        last_error: Optional[Exception] = None
        for requirements in security:
            try:
                auth = _build_auth(self._auth, requirements)
                break
            except ValueError as ve:
                last_error = ve
                continue
        else:
            assert last_error
            # due to asserts and break above, we never enter here, unless ValueError was raised
            raise last_error  # noqa
        return auth


def _build_auth(schemes: Mapping[str, httpx.Auth], requirements: SecurityRequirements) -> httpx.Auth:
    auth_flows = []
    for scheme, scopes in requirements.items():
        auth_flow = schemes.get(scheme)
        if not auth_flow:
            raise ValueError('Not authenticated', scheme)
        auth_flows.append(auth_flow)
    return MultiAuth(*auth_flows)
