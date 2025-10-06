"""Configuration repository port interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class IConfigRepository(ABC):
    """Interface for configuration persistence.

    This port defines the contract for loading and saving
    configuration settings, allowing the domain logic to be
    independent of the storage mechanism.
    """

    @abstractmethod
    def load_config(self, username: str) -> Dict[str, Any]:
        """Load configuration for a user.

        Args:
            username: Username to load config for

        Returns:
            Dictionary of configuration settings
        """
        pass

    @abstractmethod
    def save_config(self, username: str, config: Dict[str, Any]) -> bool:
        """Save configuration for a user.

        Args:
            username: Username to save config for
            config: Dictionary of configuration settings

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration settings.

        Returns:
            Dictionary of default configuration settings
        """
        pass
