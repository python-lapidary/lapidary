import inspect
from collections.abc import Iterable

import pydantic.fields
import typing_extensions as typing

T = typing.TypeVar('T')


def find_annotation(annotated: type, annotation_type: type[T]) -> tuple[type, T]:
    """Return the return type and an annotation matching type `annotation_type`."""
    assert not isinstance(annotated, typing.ForwardRef)
    return_type, *annotations = typing.get_args(annotated)
    return return_type, _find_annotation(annotations, annotation_type)


def find_field_annotation(field_info: pydantic.fields.FieldInfo, annotation_type: type[T]) -> tuple[type, T]:
    return field_info.annotation, _find_annotation(field_info.metadata, annotation_type)


def _find_annotation(annotations: Iterable[typing.Any], annotation_type: type[T]) -> T:
    matching = [
        annotation
        for annotation in annotations
        if (issubclass(annotation, annotation_type) if inspect.isclass(annotation) else isinstance(annotation, annotation_type))
    ]

    if len(matching) != 1:
        raise TypeError(f'Expected exactly one {annotation_type.__name__} annotation')
    else:
        anno = matching[0]
        if callable(anno):
            return anno()
        else:
            return anno
