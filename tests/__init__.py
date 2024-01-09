import pydantic

from lapidary.runtime import ClientBase, GET, PUT, ParamStyle, Path
from lapidary.runtime.compat import typing as ty
from lapidary.runtime.model import ReturnTypeInfo
from lapidary.runtime.model.request import RequestBody
from lapidary.runtime.model.response_map import Responses


class Cat(pydantic.BaseModel):
    id: int
    name: str


class MyClient(ClientBase):
    def __init__(self):
        super().__init__(
            base_url='http://localhost'
        )

    @GET('/cat/{id}')
    async def get_cat(
            self: ty.Self,
            *,
            id_p: ty.Annotated[int, Path('id', ParamStyle.simple)],
    ) -> ty.Annotated[Cat, Responses({
        'default': {
            'application/json': ReturnTypeInfo(Cat)
        }
    })]:
        ...

    @PUT('/cat')
    async def put_cat(
            self: ty.Self,
            *,
            body: ty.Annotated[Cat, RequestBody({'application/json': (Cat, lambda model: model.model_dump_json())})],
    ) -> ty.Annotated[Cat, Responses({
        'default': {
            'application/json': ReturnTypeInfo(Cat)
        }
    })]:
        ...


async def main() -> None:
    client = MyClient()
    await client.put_cat(body=Cat(id=1, name='Tom'))
    await client.get_cat(id_p=1)


if __name__ == '__main__':
    import anyio

    anyio.run(main)
