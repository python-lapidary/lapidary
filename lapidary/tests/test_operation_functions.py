from pprint import pp
from unittest import TestCase

from lapis.openapi import model as openapi
from lapis.render.elems.attribute import AttributeModel
from lapis.render.elems.attribute_annotation import AttributeAnnotationModel
from lapis.render.elems.client_class import get_client_class
from lapis.render.elems.refs import get_resolver
from lapis.render.elems.request_body import get_request_body_module
from lapis.render.elems.response_body import get_response_body_module
from lapis.render.elems.schema_class import SchemaClass
from lapis.render.elems.schema_module import SchemaModule
from lapis.render.module_path import ModulePath
from lapis.render.type_ref import TypeRef, GenericTypeRef, BuiltinTypeRef

model = openapi.OpenApiModel(
    openapi='3.0.3',
    info=openapi.Info(title='Lapis test schema', version='1.0.0'),
    paths=openapi.Paths(__root__={
        '/simple-response/': openapi.PathItem(
            get=openapi.Operation(
                operationId='get_simple_result',
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
                        ),
                    )}
                ),
            ),
        ),
    }))

resolve = get_resolver(model, 'lapis_test')
module_path = ModulePath('lapis_test')
union_str_absent = GenericTypeRef(module='typing', name='Union', args=[BuiltinTypeRef(name='str'), TypeRef.from_str('lapis_client_base.absent.Absent')])
common_attributes=[
                    AttributeModel(
                        name='a',
                        annotation=AttributeAnnotationModel(
                            type=union_str_absent,
                            field_props={},
                            default='lapis_client_base.absent.ABSENT',
                        ),
                    ),
                    AttributeModel(
                        name='b',
                        annotation=AttributeAnnotationModel(
                            type=union_str_absent,
                            field_props={},
                            default='lapis_client_base.absent.ABSENT',
                        ),
                    )
                ]

class OperationResponseTest(TestCase):
    def test_schema_test(self):
        pp(get_client_class(model, module_path, resolve))

    def test_response_body_schema_model(self):
        expected = SchemaModule(
            path=module_path,
            imports=[
                'lapis_client_base.absent',
                'pydantic',
            ],
            body=[SchemaClass(
                class_name='GetSchemaResponse200Response',
                base_type=TypeRef.from_str('pydantic.BaseModel'),
                attributes=common_attributes
            )]
        )

        mod = get_response_body_module(model.paths.__root__['/schema-response/'].get, module_path, resolve)
        pp(mod)

        self.assertEqual(expected, mod)

    def test_request_body_schema_class(self):
        mod = get_request_body_module(model.paths.__root__['/schema-request/'].get, module_path, resolve)
        pp(mod)

        expected = SchemaModule(
            path=module_path,
            imports=[
                'lapis_client_base.absent',
                'pydantic',
            ],
            body=[SchemaClass(
                class_name='GetSchemaRequestRequest',
                base_type=TypeRef.from_str('pydantic.BaseModel'),
                attributes=common_attributes
            )]
        )

        self.assertEqual(expected, mod)



