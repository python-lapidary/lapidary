import abc
import inspect
from collections.abc import Iterable

import pydantic.fields
import typing_extensions as typing

from .encode_param import ParamStyle, get_encode_fn
from .request import RequestContributor

if typing.TYPE_CHECKING:
    from .._httpx import ParamValue
    from .encode_param import Encoder
    from .request import RequestBuilder


T = typing.TypeVar('T')


class NameTypeAwareAnnotation(abc.ABC):
    _name: str
    _type: type

    def supply_formal(self, name: str, typ: type) -> None:
        self._name = name
        self._type = typ


class Param(RequestContributor, NameTypeAwareAnnotation, abc.ABC):
    style: ParamStyle
    alias: typing.Optional[str]
    explode: typing.Optional[bool]
    _encoder: 'typing.Optional[Encoder]'

    def __init__(self, alias: typing.Optional[str], /, *, style: ParamStyle, explode: typing.Optional[bool]) -> None:
        self.alias = alias
        self.style = style
        self.explode = explode
        self._encoder = None

    def _get_explode(self) -> bool:
        return self.explode or self.style == ParamStyle.form

    @abc.abstractmethod
    def _apply_request(self, builder: 'RequestBuilder', value: 'ParamValue'):
        pass

    def apply_request(self, builder: 'RequestBuilder', value: typing.Any) -> None:
        if not value:
            return

        if not self._encoder:
            self._encoder = get_encode_fn(self._type, self.style, self._get_explode())
        assert self._encoder
        value = self._encoder(self._name, value)
        self._apply_request(builder, value)

    @property
    def http_name(self) -> str:
        return self.alias or self._name


def find_annotation(annotated: type, annotation_type: type[T]) -> tuple[type, T]:
    """Return the return type and an annotation matching type `annotation_type`."""
    assert not isinstance(annotated, typing.ForwardRef)
    return_type, *annotations = typing.get_args(annotated)
    return _find_annotation(return_type, annotations, annotation_type)


def find_field_annotation(field_info: pydantic.fields.FieldInfo, annotation_type: type[T]) -> tuple[type, T]:
    return _find_annotation(field_info.annotation, field_info.metadata, annotation_type)


def _find_annotation(return_type: type, annotations: Iterable[typing.Any], annotation_type: type[T]) -> tuple[type, T]:
    matching = [
        annotation
        for annotation in annotations
        if not inspect.isclass(annotation) and isinstance(annotation, annotation_type) or issubclass(annotation, annotation_type)
    ]

    if len(matching) != 1:
        raise TypeError(f'Expected exactly one {annotation_type.__name__} annotation')
    else:
        anno = matching[0]
        if callable(anno):
            return return_type, anno()
        else:
            return return_type, anno
