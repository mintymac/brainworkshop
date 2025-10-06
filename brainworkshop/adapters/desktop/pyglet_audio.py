"""Pyglet implementation of the audio player port.

This adapter implements the IAudioPlayer interface using Pyglet's media API.
"""
from __future__ import annotations

import random
from pathlib import Path
from typing import Dict, List, Optional

import pyglet

from brainworkshop.ports.audio_player import IAudioPlayer


class PygletAudioPlayer(IAudioPlayer):
    """Pyglet-based audio player for sound stimuli.

    Implements audio playback using Pyglet's media API. Manages multiple
    sound channels and supports loading sound sets from resource directories.

    Attributes:
        sounds_channel1: Dictionary mapping sound names to media sources (channel 1)
        sounds_channel2: Dictionary mapping sound names to media sources (channel 2)
        player1: Pyglet media player for channel 1
        player2: Pyglet media player for channel 2
        music_player: Pyglet media player for background music
        applause_player: Pyglet media player for applause effects
        volume: Master volume level (0.0 to 1.0)
        music_volume: Music volume level (0.0 to 1.0)
        sfx_volume: Sound effects volume level (0.0 to 1.0)
    """

    def __init__(
        self,
        volume: float = 1.0,
        music_volume: float = 0.5,
        sfx_volume: float = 1.0
    ) -> None:
        """Initialize Pyglet audio player.

        Args:
            volume: Master volume level (0.0 to 1.0)
            music_volume: Music volume level (0.0 to 1.0)
            sfx_volume: Sound effects volume level (0.0 to 1.0)
        """
        self.sounds_channel1: Dict[str, pyglet.media.Source] = {}
        self.sounds_channel2: Dict[str, pyglet.media.Source] = {}

        # Create players for different channels
        self.player1 = self._create_player()
        self.player2 = self._create_player()
        self.music_player = self._create_player()
        self.applause_player = self._create_player()

        # Volume settings
        self.volume = volume
        self.music_volume = music_volume
        self.sfx_volume = sfx_volume

        # Current sound sets loaded
        self.current_set_channel1: Optional[str] = None
        self.current_set_channel2: Optional[str] = None

        # Resource paths (to be set externally)
        self.sound_resource_dir: Optional[Path] = None
        self.music_resource_dir: Optional[Path] = None

    def _create_player(self) -> pyglet.media.Player:
        """Create a new Pyglet media player.

        Returns:
            New Player instance
        """
        try:
            # Try new API (Pyglet 2.x)
            return pyglet.media.Player()
        except TypeError:
            # Fallback to old API (Pyglet 1.x)
            return pyglet.media.Player()

    def set_resource_directories(
        self,
        sound_dir: Path,
        music_dir: Optional[Path] = None
    ) -> None:
        """Set resource directories for sounds and music.

        Args:
            sound_dir: Path to sounds directory
            music_dir: Path to music directory (optional)
        """
        self.sound_resource_dir = sound_dir
        self.music_resource_dir = music_dir

    def play_sound(self, sound_name: str, channel: int = 1) -> None:
        """Play audio stimulus.

        Args:
            sound_name: Name/identifier of the sound to play
            channel: Audio channel number (1 for primary, 2 for secondary)
        """
        if channel == 1:
            sounds = self.sounds_channel1
            player = self.player1
        elif channel == 2:
            sounds = self.sounds_channel2
            player = self.player2
        else:
            return

        if sound_name not in sounds:
            # print(f"Warning: Sound '{sound_name}' not loaded in channel {channel}")
            return

        # Queue and play the sound
        try:
            player.queue(sounds[sound_name])
            player.volume = self.volume * self.sfx_volume
            player.play()
        except Exception as e:
            # Silently handle playback errors
            pass

    def play_sound_by_index(self, index: int, channel: int = 1) -> None:
        """Play sound by numeric index (1-8 typically).

        Args:
            index: Sound index (1-based)
            channel: Audio channel number
        """
        if channel == 1:
            sounds = self.sounds_channel1
        elif channel == 2:
            sounds = self.sounds_channel2
        else:
            return

        # Get list of sound names and play by index
        sound_names = sorted(sounds.keys())
        if 0 < index <= len(sound_names):
            self.play_sound(sound_names[index - 1], channel)

    def load_sound_set(self, sound_set_name: str, channel: int = 1) -> bool:
        """Load a set of sounds from resources.

        Args:
            sound_set_name: Name of the sound set to load (e.g., 'letters', 'numbers')
            channel: Audio channel number (1 for primary, 2 for secondary)

        Returns:
            True if successful, False otherwise
        """
        if self.sound_resource_dir is None:
            return False

        sound_set_dir = self.sound_resource_dir / sound_set_name
        if not sound_set_dir.exists() or not sound_set_dir.is_dir():
            return False

        # Load all audio files from directory
        sounds = {}
        for audio_file in sorted(sound_set_dir.glob('*')):
            if audio_file.suffix.lower() in ['.wav', '.mp3', '.ogg', '.flac']:
                try:
                    sound_source = pyglet.media.load(str(audio_file), streaming=False)
                    # Use filename without extension as sound name
                    sound_name = audio_file.stem
                    sounds[sound_name] = sound_source
                except Exception as e:
                    # Skip files that fail to load
                    continue

        if not sounds:
            return False

        # Store sounds in appropriate channel
        if channel == 1:
            self.sounds_channel1 = sounds
            self.current_set_channel1 = sound_set_name
        elif channel == 2:
            self.sounds_channel2 = sounds
            self.current_set_channel2 = sound_set_name

        return True

    def play_music(self, music_file: str) -> None:
        """Play background music.

        Args:
            music_file: Path to music file
        """
        if not Path(music_file).exists():
            return

        try:
            music_source = pyglet.media.load(music_file, streaming=True)
            self.music_player.queue(music_source)
            self.music_player.volume = self.volume * self.music_volume
            self.music_player.play()
        except Exception as e:
            # Silently handle music playback errors
            pass

    def play_random_music_from_dir(self, music_dir: Path) -> None:
        """Play random music file from directory.

        Args:
            music_dir: Path to directory containing music files
        """
        if not music_dir.exists() or not music_dir.is_dir():
            return

        music_files = list(music_dir.glob('*.mp3')) + \
                     list(music_dir.glob('*.ogg')) + \
                     list(music_dir.glob('*.wav'))

        if music_files:
            random_music = random.choice(music_files)
            self.play_music(str(random_music))

    def play_applause(self, applause_sounds: List[str] = None) -> None:
        """Play applause sound effect.

        Args:
            applause_sounds: List of applause sound file paths
        """
        if applause_sounds:
            applause_file = random.choice(applause_sounds)
            try:
                applause_source = pyglet.media.load(applause_file, streaming=False)
                self.applause_player.queue(applause_source)
                self.applause_player.volume = self.volume * self.sfx_volume
                self.applause_player.play()
            except Exception as e:
                pass

    def stop_all(self) -> None:
        """Stop all currently playing audio."""
        self.player1.pause()
        self.player2.pause()
        self.music_player.pause()
        self.applause_player.pause()

    def set_volume(self, volume: float) -> None:
        """Set master volume.

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.volume = max(0.0, min(1.0, volume))

    def set_music_volume(self, volume: float) -> None:
        """Set music volume.

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.music_volume = max(0.0, min(1.0, volume))
        self.music_player.volume = self.volume * self.music_volume

    def set_sfx_volume(self, volume: float) -> None:
        """Set sound effects volume.

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.sfx_volume = max(0.0, min(1.0, volume))
