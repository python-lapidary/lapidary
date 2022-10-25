import keyword
import logging
import re
import builtins
import inflection

logger = logging.getLogger(__name__)

PARAM_MODEL = 'param_model'
REQUEST_BODY = 'request_body'
RESPONSE_BODY = 'response_body'

VALID_IDENTIFIER_RE = re.compile(r'^[a-zA-Z]\w*$', re.ASCII)


def get_subtype_name(parent_name: str, schema_name: str) -> str:
    subtype_name = inflection.camelize(parent_name) + inflection.camelize(schema_name)
    subtype_name = maybe_mangle_name(subtype_name)
    logger.debug('get name for "%s" / "%s" -> "%s"', parent_name, schema_name, subtype_name)
    return subtype_name


def check_name(name: str, check_builtins=True) -> None:
    if (
            name is None
            or keyword.iskeyword(name)
            or
            (
                    check_builtins
                    and name in builtins.__dict__
            )
            or not VALID_IDENTIFIER_RE.match(name)
    ):
        raise ValueError('Invalid identifier', name)


def _escape_char(s: str) -> str:
    return 'u_{x:06x}'.format(x=ord(s))


def _mangle_name(name: str) -> str:
    name = name.replace('u_', 'u' + _escape_char('_'))
    return (
            re.sub('[^a-zA-Z]', lambda match: _escape_char(match.group()), name[0])
            + re.sub('[^a-zA-Z0-9_]', lambda match: _escape_char(match.group()), name[1:])
    )


def maybe_mangle_name(name: str, check_builtins=True) -> str:
    """
    Names that are Python keywords or in builtins get suffixed with an underscore (_).
    Names that are not valid Python identifiers or start with underscore are mangled by replacing invalid characters
    with u_{code}.
    Since 'u_' is the escaping prefix, it also gets replaced
    """
    if name is None or name == '':
        raise ValueError()

    if (
            check_builtins and (name in builtins.__dict__)
            or keyword.iskeyword(name)
    ):
        return name + '_'
    elif not VALID_IDENTIFIER_RE.match(name) or 'u_' in name:
        return _mangle_name(name)
    else:
        return name
