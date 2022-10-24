from unittest import TestCase

from lapidary_base import ParamPlacement

from lapidary.openapi import model as openapi
from lapidary.render.elems.attribute import AttributeModel
from lapidary.render.elems.attribute_annotation import AttributeAnnotationModel
from lapidary.render.elems.operation_function import get_operation_func
from lapidary.render.elems.refs import get_resolver
from lapidary.render.elems.request_body import get_request_body_module
from lapidary.render.elems.response_body import get_response_body_module
from lapidary.render.elems.schema_class_model import SchemaClass
from lapidary.render.elems.schema_module import SchemaModule
from lapidary.render.elems.type_hint import GenericTypeHint, BuiltinTypeHint, TypeHint
from lapidary.render.module_path import ModulePath

model = openapi.OpenApiModel(
    openapi='3.0.3',
    info=openapi.Info(title='Lapidary test schema', version='1.0.0'),
    paths=openapi.Paths(__root__={
        '/simple-response/': openapi.PathItem(
            get=openapi.Operation(
                operationId='get_simple_response',
                responses=openapi.Responses(__root__={
                    '200': openapi.Response(
                        description='test response',
                        content={'application/json': openapi.MediaType(
                            schema=openapi.Schema(type=openapi.Type.string),
                        )}
                    )
                })
            ),
        ),
        '/schema-response/': openapi.PathItem(
            get=openapi.Operation(
                operationId='get_schema_response',
                responses=openapi.Responses(__root__={
                    '200': openapi.Response(
                        description='test response',
                        content={'application/json': openapi.MediaType(
                            schema=openapi.Schema(
                                type=openapi.Type.object,
                                properties=dict(
                                    a=openapi.Schema(type=openapi.Type.string),
                                    b=openapi.Schema(type=openapi.Type.string),
                                ),
                                additionalProperties=False,
                            ),
                        )}
                    )
                })
            ),
        ),
        '/schema-request/': openapi.PathItem(
            get=openapi.Operation(
                operationId='get_schema_request',
                responses=openapi.Responses(__root__={}),
                requestBody=openapi.RequestBody(
                    content={'application/json': openapi.MediaType(
                        schema=openapi.Schema(
                            type=openapi.Type.object,
                            properties=dict(
                                a=openapi.Schema(type=openapi.Type.string),
                                b=openapi.Schema(type=openapi.Type.string),
                            ),
                            additionalProperties=False,
                        ),
                    )}
                ),
            ),
        ),
        '/ignored-header/': openapi.PathItem(
            get=openapi.Operation(
                operationId='ignored_header',
                responses=openapi.Responses(__root__={}),
                parameters=[
                    openapi.Parameter(
                        name='accept',
                        in_=ParamPlacement.header.value,
                    )
                ]
            ),
        ),
    }))

resolve = get_resolver(model, 'lapidary_test')
module_path = ModulePath('lapidary_test')
union_str_absent = GenericTypeHint(
    module='typing',
    name='Union',
    args=[
        BuiltinTypeHint(name='str'),
        TypeHint.from_str('lapidary_base.absent.Absent')
    ]
)
common_attributes = [
    AttributeModel(
        name='a',
        annotation=AttributeAnnotationModel(
            type=union_str_absent,
            field_props={},
            default='lapidary_base.absent.ABSENT',
        ),
    ),
    AttributeModel(
        name='b',
        annotation=AttributeAnnotationModel(
            type=union_str_absent,
            field_props={},
            default='lapidary_base.absent.ABSENT',
        ),
    )
]


class OperationResponseTest(TestCase):
    def test_response_body_schema_model(self):
        expected = SchemaModule(
            path=module_path,
            imports=[
                'lapidary_base.absent',
            ],
            body=[SchemaClass(
                class_name='GetSchemaResponse200Response',
                base_type=TypeHint.from_str('pydantic.BaseModel'),
                attributes=common_attributes
            )]
        )

        mod = get_response_body_module(model.paths.__root__['/schema-response/'].get, module_path, resolve)
        # pp(mod)

        self.assertEqual(expected, mod)

    def test_request_body_schema_class(self):
        mod = get_request_body_module(model.paths.__root__['/schema-request/'].get, module_path, resolve)

        expected = SchemaModule(
            path=module_path,
            imports=[
                'lapidary_base.absent',
            ],
            body=[SchemaClass(
                class_name='GetSchemaRequestRequest',
                base_type=TypeHint.from_str('pydantic.BaseModel'),
                attributes=common_attributes
            )]
        )

        self.assertEqual(expected, mod)

    def test_ignored_header(self):
        op_def = model.paths.__root__['/ignored-header/'].get
        op_model = get_operation_func(op_def, 'GET', '/', module_path, resolve)
        self.assertEqual([], op_model.params)
