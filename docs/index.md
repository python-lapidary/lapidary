# Lapidary

Lapidary consists of a pair of packages:

- lapidary (this project), a library that helps you write Web API clients,
- [lapidary-render](https://github.com/python-lapidary/lapidary-render/), a generator that consumes OpenAPI documents and produces API clients (that use Lapidary).

Both projects are coupled, in the sense that
lapidary-render produces output compatible with Lapidary, and
Lapidary supports the same features of OpenAPI Specification as lapidary-render.

See [this test](https://github.com/python-lapidary/lapidary/blob/develop/tests/test_client.py) for a small showcase.
