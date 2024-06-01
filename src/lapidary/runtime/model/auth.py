from collections.abc import Iterable, Mapping, MutableMapping
from typing import Optional

import httpx

from .._httpx import AuthType
from ..types_ import MultiAuth, SecurityRequirements


class AuthRegistry:
    def __init__(self, security: Optional[Iterable[SecurityRequirements]]):
        # Every Auth instance the user code authenticated with
        self._auth: MutableMapping[str, httpx.Auth] = {}

        # (Multi)Auth instance for every operation and the client
        self._auth_cache: MutableMapping[str, httpx.Auth] = {}

        # Client-wide security requirements
        self._security = security

    def resolve_auth(self, name: str, security: Optional[Iterable[SecurityRequirements]]) -> AuthType:
        if security:
            sec_name = name
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

    def authenticate(self, auth_models: Mapping[str, httpx.Auth]) -> None:
        self._auth.update(auth_models)
        self._auth_cache.clear()

    def deauthenticate(self, sec_names: Iterable[str]) -> None:
        if sec_names:
            for sec_name in sec_names:
                del self._auth[sec_name]
        else:
            self._auth.clear()
        self._auth_cache.clear()


def _build_auth(schemes: Mapping[str, httpx.Auth], requirements: SecurityRequirements) -> httpx.Auth:
    auth_flows = []
    for scheme, scopes in requirements.items():
        auth_flow = schemes.get(scheme)
        if not auth_flow:
            raise ValueError('Not authenticated', scheme)
        auth_flows.append(auth_flow)
    return MultiAuth(*auth_flows)
