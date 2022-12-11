# Lapidary - Python async OpenAPI client generator

Generate data model and client stub for OpenAPI 3.0, that are easy to understand and debug.

Leverages [Pydantic](https://github.com/pydantic/pydantic) as the base classes for models,
[HTTPX](https://github.com/encode/httpx) as the HTTP client
and [Typer](https://typer.tiangolo.com/) as the CLI library.

See [render](./lapidary-render) readme for command line interface to generate and update models and stubs.

## Supported and planned OpenAPI features

- Parameter names: operation parameters are uniquely identified by their name the value of an `in` attribute. It is possible to have parameter named `param` in all of path, query, cookies and headers.
  
  Lapidary uses Hungarian notation for method parameter names. See [issue 29](#29)
- Enums:
    
    Currently only primitive values are supported, but OpenAPI specifies no such limitation - any valid JSON value should be supported (#30). 
- oneOf, allOf, anyOf, not: see [discussion](#20) and concepts below.
    
    Currently oneOf is implemented as `typing.Union`, which is not ideal. Also Pydantic doesn't allow models to have both \_\_root__ and own properties, which isn't compatible with with OpenAPI.
- Recursive references between schemas.

    1. $ref to self: Schema A having a property, which schema is a $ref: A
    2. Indirect circular ref - schema A has a property which schema is a $ref: B and schema B has a property whose schema is $ref: A

    This could translate to a following Python code:

    ```python
    class A:
      b: 'B'
  
    class B:
      a: 'A'
    ```
    Both constructs are supported by their languages and Lapidary.

    Recursive composing or inheritance is not supported:
    ```yaml
    components:
        B:
          schema:
            oneOf:
            - $ref: /components/schemas/C // invalid
        C:
          schema:
            oneOf:
            - $ref: /components/schemas/B // invalid
    ```

- References to other schemas: unsupported.
- Read- and writeOnly properties:

   Currently rendered as not-required fields.

## APIs that contradict their specifications

Lapidary applies JSONPatch files from src/patches directory to the OpenAPI before generating the client code.

Planned: [Plug-ins](#31)

## Concepts
### Backwards and forwards compatibility

Lapidary should generate compatible client code as long as you're using
1. compatible OpenAPI spec, which includes the patches, and
2. compatible version of lapidary.

There are couple of issues that need to be solved:
1. Some unnamed elements in OpenAPI need to be named in Python.
    
    Examples:
    - enum values (list elements)
    - schema objects under requestBody and responses

2. Some names may not be valid in Python

    Examples:
    - names of all objects under /components/* names must match this regex: `^[a-zA-Z0-9\.\-_]+$`, which means characters `.-` and `_` if it's on the beginning of string must be escaped.
    - the above limitation doesn't apply to any other names, so nearly full unicode character set needs to be handled by the character escaping algorithm.

To achieve this, naming classes and variables should be independent of its siblings. E.g.

```yaml
schemas:
  A:
    type: object
    schema:
      oneOf:
      - schema:
        type: object
        properties:
          a:
            type: string
      - schema:
        type: object
        properties:
          a: integer  
```

A code generator could naively generate such python classes:
```python
class A1:
  a: str

class A2:
  a: int

A = typing.Union[A1, A2]
```

We'll forget for a moment the problem of whether `typing.Union` is a proper representation of `oneOf` schema.

The problem here is that if the OpenAPI author changes order of the two sub-schemas, that change would be backwards compatible.
On the Python side however, the generated code would have changed in an incompatible way, with properties in both A1 and A2 classes having different types than before.

In this particular case, both classes would need to be either $refs or explicitly named using an extended attribute in OpenAPI.

### Validation and type hints

OpenAPI's schema objects is a means of defining validations for JSON values, just like JSONSchema, from which it's derived.

On the other hand, Python type hints is a language feature to declare variables' (class attributes' and function parameters') types as a help for developers
through the use of static code analysis tools.

While those two goals are, to an extent, overlapping, they're not identical.

For example, a static code analysis tool is unable to check if string's length is within specified bounds. Only the application itself can check it at run-time
(perhaps by using a library, like Pydantic).

Consider these examples:

```yaml
schemas:
  A:
    properties:
      b:
        type: string
```

Could be represented as:

```python
class A:
  b: str
```

but:

```yaml
schemas:
  A:
    properties:
      b:
        type: string
        maxLength: 1
```

```python
class A(pydantic.BaseModel):
  b: typing.Annotated[str, pydantic.Field(max_length=1)]
```

Static analysis can, in the right circumstances, ensure that `b` is a string, but validating its length is only possible at run-time, in this case, by Pydantic.

In case of composite types: `anyOf`, `oneOf`, `allOf` and `not`, it may be possible to create generic type annotations for them, but it might require implementing static analysis tools to support it, or at least a plug-in for an existing tool, like Mypy.
On the other hand, validating it in run-time is relatively simple.
