import time
from functools import wraps
from loguru import logger


def log_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Chamando '{func.__name__}'")
        try:
            result = func(*args, **kwargs)
            logger.info(f"'{func.__name__}' terminou com sucesso")
            return result
        except Exception:
            logger.exception(f"'{func.__name__}' falhou")
            raise

    return wrapper


def timer_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(f"'{func.__name__}' levou {elapsed:.3f} s")
        return result

    return wrapper
