"""Application service that orchestrates game logic.

The GameController is the main application service that coordinates between
domain logic, adapters, and external interfaces. It implements the use cases
for the BrainWorkshop application.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from brainworkshop.domain.game_session import GameSession

if TYPE_CHECKING:
    from brainworkshop.models.mode import Mode
    from brainworkshop.models.stats import Stats
    from brainworkshop.ports.renderer import IRenderer
    from brainworkshop.ports.audio_player import IAudioPlayer
    from brainworkshop.ports.stats_repository import IStatsRepository
    from brainworkshop.ports.config_repository import IConfigRepository


class GameController:
    """Main application controller for BrainWorkshop.

    Orchestrates the game loop, session management, and coordination between
    domain logic and adapters. This is the primary use case implementation.

    Attributes:
        mode: Current game mode configuration
        stats: Statistics tracker
        cfg: Configuration object
        renderer: Visual rendering adapter
        audio: Audio playback adapter
        stats_repo: Stats persistence adapter
        config_repo: Config persistence adapter
        session: Current game session (None if not playing)
    """

    def __init__(
        self,
        mode: Mode,
        stats: Stats,
        cfg: Any,
        renderer: IRenderer,
        audio: IAudioPlayer,
        stats_repo: IStatsRepository,
        config_repo: IConfigRepository
    ) -> None:
        """Initialize game controller.

        Args:
            mode: Game mode configuration
            stats: Statistics tracker
            cfg: Configuration object
            renderer: Visual rendering adapter
            audio: Audio playback adapter
            stats_repo: Statistics repository
            config_repo: Configuration repository
        """
        self.mode = mode
        self.stats = stats
        self.cfg = cfg
        self.renderer = renderer
        self.audio = audio
        self.stats_repo = stats_repo
        self.config_repo = config_repo

        self.session: Optional[GameSession] = None

        # Callbacks for UI updates
        self.on_session_start: Optional[Callable] = None
        self.on_session_end: Optional[Callable] = None
        self.on_trial_start: Optional[Callable] = None
        self.on_stimulus_show: Optional[Callable] = None
        self.on_stimulus_hide: Optional[Callable] = None

    def start_new_session(
        self,
        available_audio_sets: List[str],
        available_audio2_sets: List[str]
    ) -> None:
        """Start a new training session.

        Args:
            available_audio_sets: List of available primary audio set names
            available_audio2_sets: List of available secondary audio set names
        """
        if self.session and self.session.started:
            # End current session first
            self.end_session(cancelled=True)

        # Create new session
        self.session = GameSession(self.mode, self.stats, self.cfg)

        # Wire up callbacks
        self.session.on_stimulus_generated = self._handle_stimulus_generated
        self.session.on_trial_start = self._handle_trial_start
        self.session.on_trial_end = self._handle_trial_end
        self.session.on_session_end = self._handle_session_end
        self.session.on_stimulus_hide = self._handle_stimulus_hide
        self.session.on_feedback_show = self._handle_feedback_show

        # Start session
        self.session.start(available_audio_sets, available_audio2_sets)

        # Notify UI
        if self.on_session_start:
            self.on_session_start()

    def update(self, dt: float) -> None:
        """Update game state.

        Called by the game loop at regular intervals (typically 10Hz).

        Args:
            dt: Delta time since last update
        """
        if self.session:
            self.session.update(dt)

    def register_player_input(self, modality: str) -> None:
        """Register player input for a modality.

        Args:
            modality: Modality name (position1, audio, color, etc.)
        """
        if self.session and self.session.started:
            self.session.register_input(modality)

    def end_session(self, cancelled: bool = False) -> None:
        """End current session.

        Args:
            cancelled: If True, session was cancelled (don't save stats)
        """
        if self.session:
            self.session.end(cancelled)
            self.session = None

    def pause_session(self) -> None:
        """Pause the current session."""
        if self.session:
            self.session.pause()

    def resume_session(self) -> None:
        """Resume a paused session."""
        if self.session:
            self.session.resume()

    def change_mode(self, new_mode: int) -> None:
        """Change game mode.

        Args:
            new_mode: New mode ID
        """
        if self.session and self.session.started:
            self.end_session(cancelled=True)

        self.mode.mode = new_mode
        # Mode will reconfigure itself based on new mode ID

    def change_nback_level(self, new_level: int) -> None:
        """Change N-back level.

        Args:
            new_level: New N-back level
        """
        if self.session and self.session.started:
            self.end_session(cancelled=True)

        self.mode.back = new_level
        self.mode.num_trials_total = (
            self.mode.num_trials +
            self.mode.num_trials_factor * self.mode.back ** self.mode.num_trials_exponent
        )

    def load_user_progress(self, username: str = '') -> None:
        """Load user's progress from stats repository.

        Args:
            username: Username to load progress for
        """
        # Load history
        full_history = self.stats_repo.load_user_history(username)
        self.stats.full_history = full_history

        today_sessions = self.stats_repo.get_today_sessions(username)
        self.stats.history = today_sessions

        # Count sessions
        self.stats.sessions_today = len(today_sessions)

    def save_config(self, username: str = '') -> bool:
        """Save current configuration.

        Args:
            username: Username to save config for

        Returns:
            True if successful
        """
        config_dict = self.cfg.__dict__ if hasattr(self.cfg, '__dict__') else dict(self.cfg)
        return self.config_repo.save_config(username, config_dict)

    def load_config(self, username: str = '') -> bool:
        """Load configuration for user.

        Args:
            username: Username to load config for

        Returns:
            True if successful
        """
        config_dict = self.config_repo.load_config(username)

        # Update cfg object
        for key, value in config_dict.items():
            if hasattr(self.cfg, key):
                setattr(self.cfg, key, value)
            else:
                self.cfg[key] = value

        return True

    # Internal callback handlers

    def _handle_stimulus_generated(self, stimuli: Dict[str, int]) -> None:
        """Handle stimulus generation.

        Args:
            stimuli: Generated stimuli dictionary
        """
        # Render visual stimulus
        if 'position1' in stimuli and stimuli['position1'] > 0:
            position = stimuli['position1']
            color = stimuli.get('color', 1)

            # Map color index to RGB (simplified)
            color_rgb = self._get_color_rgb(color)

            self.renderer.show_square(position, color_rgb)

        # Play audio stimulus
        if 'audio' in self.mode.modalities[self.mode.mode]:
            audio_index = stimuli.get('audio', 1)
            self.audio.play_sound_by_index(audio_index, channel=1)

        if 'audio2' in self.mode.modalities[self.mode.mode]:
            audio2_index = stimuli.get('audio2', 1)
            self.audio.play_sound_by_index(audio2_index, channel=2)

        # Notify UI
        if self.on_stimulus_show:
            self.on_stimulus_show(stimuli)

    def _handle_trial_start(self) -> None:
        """Handle trial start."""
        if self.on_trial_start:
            self.on_trial_start()

    def _handle_trial_end(self) -> None:
        """Handle trial end."""
        pass

    def _handle_session_end(self, scores: Dict[str, float], cancelled: bool) -> None:
        """Handle session end.

        Args:
            scores: Score dictionary
            cancelled: Whether session was cancelled
        """
        if not cancelled:
            # Save to repository
            session_data = {
                'timestamp': '',  # Will be set by repository
                'mode_short_name': self.mode.short_name(),
                'percent': int(scores.get('overall', 0)),
                'mode': self.mode.mode,
                'n_back': self.mode.back,
                'ticks_per_trial': self.mode.ticks_per_trial,
                'num_trials': self.mode.trial_number - 1,
                'manual': self.mode.manual,
                'session_number': self.mode.session_number,
                'category_percents': scores,
                'session_time': int(self.mode.num_trials_total * self.mode.ticks_per_trial * 0.1),
            }

            self.stats_repo.save_session(session_data)

        # Notify UI
        if self.on_session_end:
            self.on_session_end(scores, cancelled)

    def _handle_stimulus_hide(self) -> None:
        """Handle stimulus hide event."""
        self.renderer.clear_display()

        if self.on_stimulus_hide:
            self.on_stimulus_hide()

    def _handle_feedback_show(self) -> None:
        """Handle feedback display event."""
        # Could implement feedback rendering here
        pass

    def _get_color_rgb(self, color_index: int) -> tuple:
        """Map color index to RGB tuple.

        Args:
            color_index: Color index (1-8)

        Returns:
            RGB tuple (r, g, b)
        """
        # Simplified color mapping (could be made configurable)
        colors = [
            (255, 0, 0),      # Red
            (0, 255, 0),      # Green
            (0, 0, 255),      # Blue
            (255, 255, 0),    # Yellow
            (255, 0, 255),    # Magenta
            (0, 255, 255),    # Cyan
            (255, 128, 0),    # Orange
            (128, 0, 255),    # Purple
        ]

        if 1 <= color_index <= len(colors):
            return colors[color_index - 1]
        return (255, 255, 255)  # White fallback
