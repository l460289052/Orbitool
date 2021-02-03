from functools import wraps
from queue import Queue

q = Queue()


def override_input(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        if q.empty():
            return func(*args, **kwargs)
        return q.get_nowait()
    return decorator


def input(ret):
    q.put(ret)
