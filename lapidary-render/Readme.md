# Code generator
## Installation

lapidary-render requires python 3.9 or higher to run.

I recommend installing via `pipx`

`pipx install lapidary-render`

You can set python version for lapidary with `pipx install --python [path-to-python] lapidary-render`. See `pipx install --help` for details.

## Usage

`lapidary` command offers inline help and shell command completion. See `lapidary --help` for details.

### lapidary init

`lapidary init [--[no-]format] [--[no-]render] SCHEMA_PATH PROJECT_ROOT PACKAGE_NAME`

Lapidary will create 
- PROJECT_ROOT and all necessary directories,
- \_\_init\_\_.py files,
- pyproject.toml with [poetry](https://python-poetry.org/) configured,
- py.typed
- client.pyi with function stubs for all operations and a client.py with an empty client class.
- [Pydantic](https://docs.pydantic.dev/) model classes for each schema.

All python files are generated in PROJECT_ROOT/gen directory.

If a directory PROJECT_ROOT/src/patches exists, Lapidary will read all yaml files and apply them as JSONPatch against the original openapi file.

If the original openapi file is not compatible with Lapidary, running `lapidary init --no-render ...` will generate only the project structure without any
models or stubs. Once you've prepared the patch, run `lapidary update`.

### lapidary update

`lapidary update [--[no-]format] [--[no-]cache] [PROJECT_ROOT]`

Default PROJECT_ROOT is the current directory.

The command
- deletes PROJECT_ROOT/gen directory,
- re-applies patches to openapi file
- and generates python files

### lapidary version

`lapidary version`

Prints the programs version and exits.

## Configuration

Lapidary can be configured with a pyproject.yaml file, under [tool.lapidary] path.

Only `package` value is required, and it's set by `lapidary init`.

- package [str] - root package name 
- format [bool] - whether to format the generated code with black [default = True].
- cache [bool] - whether to cache openapi and patches as pickle files. Only files larger than 50kB are cached [default = True].
- src_root [str] - sources root, in PROJECT_ROOT [default = 'src'].
- gen_root [str] = generated sources root, in PROJECT_ROOT [default = 'gen'].
- patches [str] = patches directory, under sources root [default = 'patches'].
