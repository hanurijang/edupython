from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable


_memory: dict[str, tuple[float, Any]] = {}


def get_cached(key: str, ttl_sec: int, loader: Callable[[], Any]) -> Any:
    now = time.time()
    cached = _memory.get(key)
    if cached and now - cached[0] < ttl_sec:
        return cached[1]

    value = loader()
    _memory[key] = (now, value)
    return value


def clear_cache(prefix: str | None = None) -> None:
    if prefix is None:
        _memory.clear()
        return
    for key in list(_memory):
        if key.startswith(prefix):
            del _memory[key]


def cached(ttl_sec: int, key_builder: Callable[..., str]):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = key_builder(*args, **kwargs)
            return get_cached(key, ttl_sec, lambda: func(*args, **kwargs))

        return wrapper

    return decorator
