from slowapi import Limiter


def build_limiter(default_limit: str, storage_uri: str) -> Limiter:
    return Limiter(key_func=lambda request: "")
