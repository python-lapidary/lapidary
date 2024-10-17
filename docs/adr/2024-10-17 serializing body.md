# Serializing request body

## The Current solution (0.11.0)

Currently lapidary checks type of value of the body parameter and tries to match against the type map passed to the `Body` annotation.

Problem starts when body is a collection: `type()` returns the type of only the collection (e.g. `list`), so the type matching fails.

## Possible alternatives

1. Check the type of the first item, but there's never a guarantee that the passed collection is homogenic.
Both JSON Schema and python typing support heterogenic collections.

2. Check type of all items is out of the question for performance reasons, and pydantic does it anyway during serialization.

3. Try to serialize the value with a TypeAdapter for each type in the type map. The first successful attempt also determines the body content type.
4. Either accept extra parameter `body_type: type` or accept body as tuple with the type explicitly declared: `body: T | Union[T, type]`.

The last two solutions seem feasible.
Trying every type would incur a performance hit for unions of complex types, but
- it would handle simpler cases well,
- keep lapidary compatible with lapidary-render,

Lapidary could still accept optional type parameter but use the other method as a fallback for when user doesn't pass the type.

# Accepted solution

Lapidary will not check the type of body value, instead it will try serializing it with every type mentioned in the type map in `Body` annotation.

Lapidary should implement an optional explicit body type parameter in a future version, either as a separate parameter, or as a tuple together with the body value.
