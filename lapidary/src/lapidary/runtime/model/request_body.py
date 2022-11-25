from typing import Optional

import inflection
from mimeparse import best_match

from .refs import ResolverFunc
from .type_hint import TypeHint, resolve_type_hint
from .. import openapi
from ..http_consts import MIME_JSON
from ..module_path import ModulePath


def get_request_body_type(op: openapi.Operation, module: ModulePath, resolve: ResolverFunc) -> Optional[TypeHint]:
    mime_json = best_match(op.requestBody.content.keys(), MIME_JSON)
    if mime_json == '':
        return None
    schema = op.requestBody.content[mime_json].schema_
    return resolve_type_hint(schema, module, request_type_name(op.operationId), resolve)


def request_type_name(name):
    return inflection.camelize(name) + 'Request'
