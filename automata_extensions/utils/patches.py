"""Targeted runtime compatibility fix for cached_method 0.1.0."""

from __future__ import annotations

from collections.abc import Callable
from importlib.metadata import version
from typing import cast

from cached_method import cached_method  # type: ignore[import-untyped]


_original_get: Callable[
    [cached_method, object | None, type[object] | None], object
] = cached_method.__get__


class _LiveBoundCall:
    """Keep the instance alive only while the returned callable exists."""

    __slots__ = ("_instance", "_cache")

    def __init__(self, instance: object, cache: Callable[..., object]) -> None:
        self._instance = instance
        self._cache = cache

    def __call__(self, *args: object, **kwargs: object) -> object:
        return self._cache(*args, **kwargs)

    def __getattr__(self, name: str) -> object:
        # Preserve cache_info/cache_clear and metadata of the cached call.
        return getattr(self._cache, name)


def _patched_get(
    descriptor: cached_method,
    instance: object | None,
    owner: type[object] | None = None,
) -> object:
    cached = _original_get(descriptor, instance, owner)
    if instance is None:
        return cached
    return _LiveBoundCall(instance, cast(Callable[..., object], cached))


def patch_cached_method() -> bool:
    """Patch cached_method's weak descriptor without replacing its cache.

    The 0.1.0 descriptor stores an LRU callable containing a weak method on
    each instance. On a temporary automaton, the returned callable does not
    keep the instance alive until invocation. This patch delegates cache
    creation and lookup to the original descriptor, then returns a temporary
    wrapper holding the instance strongly for the duration of that call.
    Neither the instance nor the cache retains this wrapper. Calls on the
    class return the original descriptor.

    Returns
    -------
    bool
        True if this call installed the patch; False if it was active.

    Raises
    ------
    RuntimeError
        If the installed dependency version or descriptor differs from the
        inspected cached_method 0.1.0 implementation.

    Complexity
    ----------
    O(1) time and space per patch call. Each descriptor access adds O(1)
    time and one short-lived wrapper; the existing cache retains its own
    runtime and memory costs.

    References
    ----------
    Mature documentation section 11 and its executed chained-call example;
    cached_method 0.1.0 source; ADR-0025.
    """
    if cached_method.__get__ is _patched_get:
        return False
    if (
        version("cached_method") != "0.1.0"
        or _original_get.__module__ != "cached_method"
        or _original_get.__qualname__ != "cached_method.__get__"
        or cached_method.__get__ is not _original_get
    ):
        raise RuntimeError("unsupported cached_method descriptor version")
    cached_method.__get__ = _patched_get
    return True
