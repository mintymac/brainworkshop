"""File-based configuration repository implementation.

This adapter implements the IConfigRepository interface using INI files
for configuration storage, matching the original BrainWorkshop format.
"""
from __future__ import annotations

import configparser
from pathlib import Path
from typing import Any, Dict, Optional

from brainworkshop.ports.config_repository import IConfigRepository


class FileConfigRepository(IConfigRepository):
    """INI file-based config storage.

    Implements configuration persistence using ConfigParser and INI files.
    Supports per-user config files and default configuration.

    Attributes:
        config_dir: Directory containing config files
        default_config: Default configuration dictionary
    """

    def __init__(
        self,
        config_dir: Path,
        default_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize file config repository.

        Args:
            config_dir: Directory for config files
            default_config: Default configuration dictionary
        """
        self.config_dir = config_dir
        self.default_config = default_config or {}

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self, username: str = 'default') -> Dict[str, Any]:
        """Load configuration for a user.

        Args:
            username: Username to load config for

        Returns:
            Dictionary of configuration settings
        """
        config_file = self._get_config_path(username)

        if not config_file.exists():
            # Return default config if user config doesn't exist
            return self.get_default_config()

        try:
            parser = configparser.ConfigParser()
            parser.read(config_file)

            # Convert ConfigParser to dict
            config_dict = {}
            for section in parser.sections():
                for key, value in parser.items(section):
                    # Try to convert to appropriate type
                    config_dict[key.upper()] = self._parse_value(value)

            # Also check for DEFAULT section
            for key, value in parser.items('DEFAULT'):
                if key.upper() not in config_dict:
                    config_dict[key.upper()] = self._parse_value(value)

            return config_dict

        except Exception as e:
            print(f"Error loading config for {username}: {e}")
            return self.get_default_config()

    def save_config(self, username: str, config: Dict[str, Any]) -> bool:
        """Save configuration for a user.

        Args:
            username: Username to save config for
            config: Dictionary of configuration settings

        Returns:
            True if successful, False otherwise
        """
        config_file = self._get_config_path(username)

        try:
            parser = configparser.ConfigParser()

            # Add settings to DEFAULT section
            for key, value in config.items():
                parser.set('DEFAULT', key.lower(), str(value))

            # Write to file
            with open(config_file, 'w') as f:
                parser.write(f)

            return True

        except Exception as e:
            print(f"Error saving config for {username}: {e}")
            return False

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration settings.

        Returns:
            Dictionary of default configuration settings
        """
        return dict(self.default_config)

    def _get_config_path(self, username: str) -> Path:
        """Get path to config file for username.

        Args:
            username: Username

        Returns:
            Path to config file
        """
        if username == 'default':
            return self.config_dir / 'config.ini'
        else:
            return self.config_dir / f'{username}-config.ini'

    def _parse_value(self, value: str) -> Any:
        """Parse string value to appropriate type.

        Args:
            value: String value from INI file

        Returns:
            Parsed value (int, float, bool, or str)
        """
        # Try boolean
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        if value.lower() in ('false', 'no', '0', 'off'):
            return False

        # Try int
        try:
            if '.' not in value:
                return int(value)
        except ValueError:
            pass

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value

    def config_exists(self, username: str) -> bool:
        """Check if config file exists for user.

        Args:
            username: Username to check

        Returns:
            True if config exists
        """
        return self._get_config_path(username).exists()

    def delete_config(self, username: str) -> bool:
        """Delete config file for user.

        Args:
            username: Username to delete config for

        Returns:
            True if successful, False otherwise
        """
        config_file = self._get_config_path(username)

        if not config_file.exists():
            return True

        try:
            config_file.unlink()
            return True
        except Exception as e:
            print(f"Error deleting config for {username}: {e}")
            return False
