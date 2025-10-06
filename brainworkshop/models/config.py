"""Configuration models."""
from __future__ import annotations

from typing import Any


class dotdict(dict):
    """Dictionary subclass enabling attribute-style access to dictionary keys.

    Provides convenient dot notation access to dictionary items, allowing both
    dict['key'] and dict.key syntax for getting, setting, and deleting items.
    Used throughout the application for configuration objects.

    Example:
        d = dotdict({'foo': 1, 'bar': 2})
        d.foo  # Returns 1
        d.baz = 3  # Sets d['baz'] = 3
        del d.foo  # Removes 'foo' from dictionary

    Attributes:
        Inherits all dict attributes and items can be accessed as attributes.
    """
    def __getattr__(self, attr: str) -> Any:
        return self.get(attr, None)
    __setattr__= dict.__setitem__
    __delattr__= dict.__delitem__
