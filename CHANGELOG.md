# Change Log
This project adheres to [Semantic Versioning](http://semver.org/).

## [Next]
### Changed
- Use multiprocessing to speed-up code generation.

## [0.5.0] 2022-10-03
### Added
- Exception types
- limited support for allOf schemas
- optional explicit names for enum values

### Changed
- Generated clients are now context managers
- Sort model attributes

### Fixed
- cache directory doesn't exist
- pydantic model Config classes
- read- and writeOnly properties were required
- inclusive/exclusive minimum mixed

## [0.4.0] 2022-09-29
### Added
- Added subcommands `update` and `init`, `update` reads configuration from pyproject.toml .
- ApiClient accepts base URL, the first server declared in schema is used as the default.
- Extended schema with global headers element; passing it as headers to httpx.AsyncClient().
- Added support for a single API Key authentication.
- Added support for naming schema classes
- Generate classes for schemas declared in-line under allOf, onyOf and oneOf.
- global responses

### Changed
- Rename project to Lapidary

### Fixed
- module name for response body schema class
- required params had default value ABSENT

## [0.3.1] 2022-09-20
### Fixed
- loading resources when installed from whl
- computing TypeRef hash
- writing pyproject to non-existent directory

## [0.3.0] 2022-09-20
### Changed
- Support Python 3.9

## [0.2.0]
### Added
- Support simple oneOf schemas
- Support errata, a JSON Patch for the specification
- support for request and response body

### Changed
- lapis is now an executable

### Fixed
- Regex field value
- handling of type hints and imports

## [0.1.2] - 2022-09-14
### Changed
- Renamed project due to a name conflict in PyPY


## [0.1.0] - 2022-09-14
### Added
- Generate classes for schemas under components/schemas
- Generate partial client class with methods based on /paths/*/*

