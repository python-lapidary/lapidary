# Lapis - Python OpenAPI client generator

Generate OpenAPI 3.0.3 client code that is easy to understand and debug.

Leverages [Pydantic](https://github.com/pydantic/pydantic) as the base classes
and [httpx](https://github.com/encode/httpx) as the HTTP client.

## Usage

lapis [--errata path] spec_file target_dir root_package

Lapis will create target_dir, all necessary directories and pyproject.toml if they don't exist.

Generated files will be placed in <target_dir>/gen/<root_package>

Errata is a JSON Patch file in JSON or YAML format; it's applied to the spec before any other processing.

## Supported OpenAPI features

- Parameter names: operation parameters are uniquely identified by their name the value of an `in` attribute. It is possible to have parameter named `param` in all of path, query, cookies and headers.
  
  Lapis uses Hungarian notation for method parameter names.
- Enums: [TODO] there's no limitation that enum schema cannot be an object or an array.

  Enums might need two python classes - a subclass of `enum.Enum` and the schema class.
- oneOf: maps to typing.Union
- AllOf: [TODO] maps to a separate class that uses all the schemas as superclasses.
- AnyOf: [TODO] maps to similar class as in case of AllOf, all fields should be non-required and the object should validate against at least one of superclasses.
- Recursive references between schemas: supported.
- References to other schemas: unsupported.
- Read- and write-only attributes: [TODO] Read-only attributes are considered non-existent when the object is validated before being sent to the server.

## Broken and incomplete API specifications

- errata: use errata to update the specification document in cases where actual data doesn't match it, and the service provider is reluctant or slow to update it.

TODO: pre- and postprocessing of API specification (dict- and pydantic-based models) with python code, errata (jsonpatch), etc

## Backwards compatibility

Once stable, Lapis should generate code that is backwards compatible as long as the API specification is too. The following rules are used to ensure that.

Names of interface elements (public functions, classes and methods) are fully deterministic and are derived only from their source elements and, in some cases, their parents.
For example, schemas of the same name are either placed in separate modules, or their names have the parent element name prepended. 

Each operation must have operationId which is used to create a unique package for its models.

The structure of the API specification is roughly reflected in the generated code.
Each schema under #/components/schemas together with all inline parameter schemas will become a single module in `<your_package>.components.schemas`.
Each operation must define `operationId` which will be used as a sub-package name for the module containing its all inline schemas. Operation packages will be placed under `<your_package>.paths`

