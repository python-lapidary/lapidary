import abc
import logging
from collections.abc import Awaitable, Callable, Iterable, Mapping, MutableMapping
from importlib.metadata import version
from typing import Any, Optional

import httpx

from .auth import AuthType, MultiAuth, NamedAuth, SecurityRequirements
from .model.op import OperationModel, get_operation_model
from .request import build_request

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
        headers = httpx.Headers(httpx_kwargs.pop('headers', None)) or httpx.Headers()
        if user_agent:
            headers['User-Agent'] = user_agent

        self._client = _http_client or httpx.AsyncClient(base_url=base_url, headers=headers, **httpx_kwargs)
        self._security = security
        self._lapidary_operations: MutableMapping[str, OperationModel] = {}
        self._auth: MutableMapping[str, httpx.Auth] = {}
        self._auth_cache: MutableMapping[str, httpx.Auth] = {}

    async def __aenter__(self):
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
            self._client.build_request,
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

    def lapidary_authenticate(self, *auths: NamedAuth) -> None:
        self._auth.update(auths)
        self._auth_cache.clear()

    def lapidary_deauthenticate(self, *sec_names: str) -> None:
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
            # due to assert and break above, we never enter here, unless ValueError was raised
            raise last_error  # noqa
        return auth


def _build_auth(schemes: Mapping[str, httpx.Auth], requirements: SecurityRequirements) -> httpx.Auth:
    auth_flows = []
    for scheme, scopes in requirements.items():
        auth_flow = schemes.get(scheme)
        if not auth_flow:
            raise ValueError('Not authenticated', scheme)
        if scopes and 'scope' in dir(auth_flow) and auth_flow.scope != scopes:
            raise ValueError('scope', auth_flow, scopes)
        auth_flows.append(auth_flow)
    return MultiAuth(*auth_flows)
