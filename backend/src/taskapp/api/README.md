# api
HTTP layer: routers, request/response schemas, error mapping.
May import: `application`, `domain`, FastAPI and Pydantic.
Must not import: `infrastructure` (wiring happens in the composition root).
Routers are thin: parse input, call one use case, map the result.
Domain errors map to HTTP responses in a single place.
