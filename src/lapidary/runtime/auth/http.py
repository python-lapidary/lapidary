from typing import Optional

from .api_key import ApiKeyAuth
from ..model.params import ParamLocation


class HTTPAuth(ApiKeyAuth):
    def __init__(self, scheme: str, token: str, bearer_format: Optional[str] = None):
        value_format_ = bearer_format if bearer_format and scheme.lower() == 'bearer' else '{token}'
        super().__init__(
            api_key=value_format_.format(token=token),
            name='Authorization',
            placement=ParamLocation.header,
        )
