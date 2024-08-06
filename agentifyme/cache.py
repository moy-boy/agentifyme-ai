import os
import functools
import hashlib
from enum import Enum
from typing import TypeVar, Callable, Any, ParamSpec, Optional, Generic, Dict
from abc import ABC, abstractmethod

import joblib

P = ParamSpec("P")
R = TypeVar("R", bound=Callable[..., Any])
T = TypeVar("T")


class CacheType(str, Enum):
    """Cache types."""

    MEMORY = "memory"
    DISK = "disk"
    NONE = "none"


class Cache(ABC, Generic[T]):
    """
    Abstract base class for cache implementations.

    Args:
        T: The type of values stored in the cache.

    Attributes:
        None

    Methods:
        get: Retrieve a value from the cache.
        set: Set a value in the cache.
    """

    @abstractmethod
    def get(self, key: str) -> Optional[T]:
        """
        Retrieve a value from the cache.

        Args:
            key: The key associated with the value to retrieve.

        Returns:
            The value associated with the given key, or None if the key is not found.
        """

    @abstractmethod
    def set(self, key: str, value: T) -> None:
        """
        Set a value in the cache.

        Args:
            key: The key to associate with the value.
            value: The value to store in the cache.

        Returns:
            None
        """


class MemoryCache(Cache[T]):
    """
    A simple in-memory cache implementation.

    This cache stores key-value pairs in memory and provides methods to get and set values.

    Attributes:
        cache (Dict[str, T]): The dictionary that holds the cached values.

    """

    def __init__(self):
        self.cache: Dict[str, T] = {}

    def get(self, key: str) -> Optional[T]:
        """
        Get the value associated with the given key.

        Args:
            key (str): The key to retrieve the value for.

        Returns:
            Optional[T]: The value associated with the key, or None if the key is not found.

        """
        return self.cache.get(key, None)

    def set(self, key: str, value: T) -> None:
        """
        Set the value for the given key.

        Args:
            key (str): The key to set the value for.
            value (T): The value to be stored.

        Returns:
            None

        """
        self.cache[key] = value


class DiskCache(Cache[T]):
    """
    A disk-based cache implementation that stores objects using joblib.

    Args:
        cache_dir (str, optional): The directory path where the cache files will be stored.
            Defaults to "/tmp/agentifyme-cache".

    Attributes:
        cache_dir (str): The directory path where the cache files are stored.

    """

    def __init__(self, cache_dir: str = "/tmp/agentifyme-cache"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def get(self, key: str) -> Optional[T]:
        """
        Retrieve the value associated with the given key from the cache.

        Args:
            key (str): The key used to identify the value in the cache.

        Returns:
            Optional[T]: The value associated with the key, or None if the key does not exist in the cache.

        """
        file_path = os.path.join(self.cache_dir, key)
        if os.path.exists(file_path):
            return joblib.load(file_path)
        return None

    def set(self, key: str, value: T) -> None:
        """
        Store the given value in the cache with the specified key.

        Args:
            key (str): The key used to identify the value in the cache.
            value (T): The value to be stored in the cache.

        """
        file_path = os.path.join(self.cache_dir, key)
        joblib.dump(value, file_path)


class NoCache(Cache[T]):
    """
    A cache implementation that does not store any values.

    This cache implementation always returns `None` when `get` is called,
    and does nothing when `set` is called.

    Attributes:
        None

    Methods:
        get(key: str) -> Optional[T]: Returns `None` for any given key.
        set(key: str, value: T) -> None: Does nothing.
    """

    def get(self, key: str) -> Optional[T]:
        return None

    def set(self, key: str, value: T) -> None:
        pass


def cache_factory(cache_type: CacheType) -> Cache[T]:
    """
    Factory function to create a cache based on the given cache_type.

    Args:
        cache_type (CacheType): The type of cache to create.

    Returns:
        Cache[T]: An instance of the cache based on the cache_type.

    """
    if cache_type == CacheType.MEMORY:
        return MemoryCache()
    elif cache_type == CacheType.DISK:
        return DiskCache()

    # default to no cache
    return NoCache()


F = TypeVar("F", bound=Callable[..., Any])


def cache(cache_type: CacheType = CacheType.NONE) -> Callable[[F], F]:
    """
    Decorator that caches the result of a function based on its arguments.

    Args:
        cache_type (CacheType, optional): The type of cache to use. Defaults to CacheType.NONE.

    Returns:
        Callable[[F], F]: The decorated function.

    """

    def decorator(func: F) -> F:
        cache_instance: Cache[Any] = cache_factory(cache_type)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Exclude 'self' from args if present
            if args and hasattr(args[0], func.__name__):
                actual_args = args[1:]
            else:
                actual_args = args

            # Create a unique key based on the function name and arguments
            args_str = str(actual_args) + str(kwargs)
            key = hashlib.md5(args_str.encode()).hexdigest()

            # Check cache for the key
            result = cache_instance.get(key)
            if result is not None:
                return result

            # Call the function and cache the result
            result = func(*args, **kwargs)
            cache_instance.set(key, result)
            return result

        return wrapper  # type: ignore

    return decorator
