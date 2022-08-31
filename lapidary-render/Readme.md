# Lapis - Python API client generator



## Future compatibility

Generated interfaces (names of API client classes and methods, request and response body classes) should be stable between versions, as long as versions of the
API specification are compatible.

Names of interface elements must be derived only form their source elements, and be independent of existence of other elements. Can't
have a number appended to a name just to avoid a name clash.

Elements of interface:

- API client classes
- methods corresponding to operations
- method parameters
- request and response body models

It's not possible to generate future-proof class names for anonymous schemas defined in-line in `allOf`, `anyOf` or `oneOf`, unless 
