import sys
import typing

if sys.version_info >= (3, 10):
    # python 3.10 syntax `type | type` creates types.UnionType instance
    import types

    UNION_TYPES = (types.UnionType, typing.Union)
else:
    UNION_TYPES = (typing.Union,)
