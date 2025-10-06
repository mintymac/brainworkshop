"""Audio player port interface."""
from __future__ import annotations

from abc import ABC, abstractmethod


class IAudioPlayer(ABC):
    """Interface for playing audio stimuli.

    This port defines the contract for audio playback, allowing
    the domain logic to be independent of the specific audio
    technology (Pyglet, Web Audio API, etc.).
    """

    @abstractmethod
    def play_sound(self, sound_name: str, channel: int = 1) -> None:
        """Play audio stimulus.

        Args:
            sound_name: Name/identifier of the sound to play
            channel: Audio channel number (1 for primary, 2 for secondary)
        """
        pass

    @abstractmethod
    def load_sound_set(self, sound_set_name: str, channel: int = 1) -> bool:
        """Load a set of sounds from resources.

        Args:
            sound_set_name: Name of the sound set to load (e.g., 'letters', 'numbers')
            channel: Audio channel number (1 for primary, 2 for secondary)

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def stop_all(self) -> None:
        """Stop all currently playing audio."""
        pass
