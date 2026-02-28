"""重试机制"""
import time
import logging
from functools import wraps
from typing import Callable, Type, Tuple

logger = logging.getLogger(__name__)


def retry_on_exception(
    exceptions: Tuple[Type[Exception], ...],
    maxtries: int = 3,
    backoff: float = 2.0,
    exponential: bool = True,
):
    """异常重试装饰器

    Args:
        exceptions: 需要捕获的异常类型
        maxtries: 最大重试次数
        backoff: 基础退避时间（秒）
        exponential: 是否使用指数退避
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tries = 0
            while tries < maxtries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    tries += 1
                    if tries >= maxtries:
                        logger.error(
                            f"Function {func.__name__} failed after {maxtries} attempts: {e}"
                        )
                        raise

                    wait_time = backoff * (exponential ** (tries - 1))
                    logger.warning(
                        f"Function {func.__name__} attempt {tries}/{maxtries} failed: {e}. "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)

            return None
        return wrapper
    return decorator