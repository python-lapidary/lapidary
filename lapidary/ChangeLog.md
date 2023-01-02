# Change Log
This project adheres to [Semantic Versioning](http://semver.org/).

## [Next]

## [0.8.0](https://github.com/python-lapidary/lapidary/releases/tag/v0.8.0) - 2023-01-02
### Added
- Support for arbitrary specification extensions (x- properties).
- Support iterator result and paging plugin.

### Fixed
- Property cross-validation (e.g. only one property of example and examples is allowed).
- Bearer security scheme.

## [0.7.3](https://github.com/python-lapidary/lapidary/releases/tag/v0.7.3) - 2022-12-15
### Fixed
- None error on missing x-lapidary-responses-global
- Enum params are rendered as their string representation instead of value.

## [0.7.2](https://github.com/python-lapidary/lapidary/releases/tag/v0.7.2) - 2022-12-15
### Fixed
- platformdirs dependency missing from pyproject.

## [0.7.1](https://github.com/python-lapidary/lapidary/releases/tag/v0.7.1) - 2022-12-15
### Fixed
- Error while constructing a type.

## [0.7.0](https://github.com/python-lapidary/lapidary/releases/tag/v0.7.0) - 2022-12-15
### Added
- Support for api responses.
- py.typed for mypy
- Support auth object.

### Changed
- Migrated project to monorepo
- Unified versioning lapidary-render
- Changed some models to better suite a dynamic library.

### Fixed
- Dynamically creating generic types
