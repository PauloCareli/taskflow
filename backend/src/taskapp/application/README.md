# application
Use cases, ports (interfaces) and DTOs.
May import: `domain` and the standard library.
Must not import: `infrastructure`, `api`, FastAPI, SQLAlchemy, Celery.
Use cases receive ports through their constructor and raise domain errors.
Never accept or return ORM models or Pydantic schemas.
