import enum


class ParamDirection(enum.Flag):
    """Use read for readOnly, write for writeOnly; read+write if unset"""

    read = enum.auto()
    write = enum.auto()


class ParamLocation(enum.Enum):
    cookie = 'cookie'
    header = 'header'
    path = 'path'
    query = 'query'


ParamPlacement = ParamLocation
