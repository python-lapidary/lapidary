from lapidary.runtime import openapi
from lapidary.runtime.http_consts import MIME_JSON
from lapidary.runtime.model import get_client_model, get_resolver, ClientModel, ClientInit, OperationModel
from lapidary.runtime.model.response_map import ReturnTypeInfo
from lapidary.runtime.module_path import ModulePath
from lapidary.runtime.openapi import LapidaryModelType


def test_parse_iterator():
    oa_model = openapi.OpenApiModel(
        openapi='3.0.3',
        info=openapi.Info(
            title='test',
            version='1',
        ),
        paths=openapi.Paths(**{
            '/': openapi.PathItem(
                get=openapi.Operation(
                    operationId='test_op',
                    responses=openapi.Responses(**{
                        '200': openapi.Response(
                            description='',
                            content={MIME_JSON: openapi.MediaType(schema_=openapi.Schema(
                                type=openapi.Type.array,
                                items=openapi.Schema(
                                    type=openapi.Type.string
                                ),
                                lapidary_model_type=LapidaryModelType.iterator,
                            ))},
                        )
                    })
                )
            )
        }),
    )
    model = get_client_model(oa_model, ModulePath('test'), get_resolver(oa_model, 'test'))
    expected = ClientModel(
        init_method=ClientInit(default_auth=None),
        methods={
            'test_op': OperationModel(
                method='get',
                path='/',
                params_model=None,
                response_map={
                    '200': {
                        MIME_JSON: ReturnTypeInfo(list[str], True)
                    }
                },
                paging=None
            )
        }
    )

    assert model == expected
