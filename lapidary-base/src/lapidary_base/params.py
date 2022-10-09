import enum


class ParamDirection(enum.Flag):
    read = enum.auto()
    write = enum.auto()


class ParamLocation(enum.Enum):
    cookie = 'cookie'
    header = 'header'
    path = 'path'
    query = 'query'


ParamPlacement = ParamLocation
