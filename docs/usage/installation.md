# Installation

Lapidary is a library, you can add it to your existing project, but I recommend creating a separate project for each remote service.

## Using poetry

With `poetry` you can install `lapidary` simply by typing:
```shell
poetry add lapidary
```

## Using lapidary-render

If you have OpenAPI 3.0 document, you can initialize a project with lapidary-render:

```shell
lapidary-render init
```

or via pipx:

```shell
pipx run lapidary-render init
```

See [the documentation](/lapidary-render/) for more details.
