from dataclasses import dataclass

import httpx
import httpx_auth

from .. import openapi


@dataclass(frozen=True)
class OAuth2:
    user_name: str
    password: str

    def create(self, model: openapi.SecurityScheme) -> httpx.Auth:
        return httpx_auth.OAuth2ResourceOwnerPasswordCredentials(
            token_url=model.__root__.flows.password.tokenUrl,
            username=self.user_name,
            password=self.password,
        )
