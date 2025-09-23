# Lapidary

[![test](https://github.com/python-lapidary/lapidary/actions/workflows/test_publish.yaml/badge.svg)](https://github.com/python-lapidary/lapidary/actions/workflows/test_publish.yaml)

Python Helper for Web API clients.

## Why

Web API clients follow a relatively small set of patterns and implementing them is rather repetitive task.
Prepare request, make the call, handle response status, deserialize the body
Typical examples show how to use `request.get()` or similar method, but this is an anti-pattern. These calls should be encapsulated as module functions or methods.

## How

Lapidary is a library that provides decorators and annotations for describing Web APIs in a way similar to OpenAPI.
In fact [lapidary render](https://github.com/python-lapidary/lapidary-render/) can convert much of OpenAPI 3.0 to Lapidary code.

At runtime, the library interprets user-provided function declarations and makes them behave as specified.
If a function accepts parameter of type `X` and returns `Y`, Lapidary will try to convert `X` to HTTP request and the response back to `Y`.

Check the [example](https://python-lapidary.github.io/lapidary/#usage)
