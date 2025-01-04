import asyncio
from functools import wraps
from typing import Callable


def coro(f: Callable):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper
