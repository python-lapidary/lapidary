import enum


class ParamDirection(enum.Flag):
    read = enum.auto()
    write = enum.auto()


class ParamPlacement(enum.Enum):
    cookie = 'cookie'
    header = 'header'
    path = 'path'
    query = 'query'
