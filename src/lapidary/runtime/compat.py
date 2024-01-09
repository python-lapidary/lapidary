__all__ = ['typing']

import sys

if sys.version_info < (3, 12):
    import typing_extensions as typing
else:
    import typing
