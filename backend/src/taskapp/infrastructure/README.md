# infrastructure
Adapters for the ports: database, JWT and hashing, Celery, settings.
May import: `domain`, `application` and third-party libraries.
Must not import: `api`.
Repositories never commit; the unit of work owns transactions.
Pydantic is allowed here only for settings.
