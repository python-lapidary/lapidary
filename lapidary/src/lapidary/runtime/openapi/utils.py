from typing import Iterator, Union

from . import model as openapi


def get_operations(
        path_item: openapi.PathItem,
        skip_reference=False,
) -> Iterator[tuple[str, Union[openapi.Operation, openapi.Reference]]]:
    for op_name in path_item.__fields_set__:
        v = getattr(path_item, op_name)
        if (
                isinstance(v, openapi.Operation)
                or (not skip_reference and isinstance(v, openapi.Reference))
        ):
            yield op_name, v
