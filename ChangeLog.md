# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html),
and the format of this file is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.9.0]
### Added
- Added a default user-agent header.
- Added support for security scheme combinations.

### Changed
- Changed the programming paradigm from dynamic with scaffolding to declarative via annotations.
- Changed authentication model to NamedAuth.
- Updated required python version to 3.9, following httpx-auth

### Removed
- Removed support for invalid HTTP status codes patterns, like 20X ([OAS3.1 4.8.16.2](https://spec.openapis.org/oas/v3.1.0#patterned-fields-0)).
- Removed Absent class #50.

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
