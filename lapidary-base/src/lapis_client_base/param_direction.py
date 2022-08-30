import enum


class ParamDirection(enum.Flag):
    read = enum.auto()
    write = enum.auto()
