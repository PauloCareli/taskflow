# domain
Pure business rules: entities, value objects, enums, domain errors.
May import: the Python standard library only.
Must not import: `application`, `infrastructure`, `api`, FastAPI, SQLAlchemy, Pydantic, Celery.
Use dataclasses and enums; no framework types, no settings, no `datetime.now()`.
