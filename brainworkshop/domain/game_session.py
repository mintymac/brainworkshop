"""Core game session logic - platform independent.

This module contains the GameSession class that manages the state machine
for an N-back training session, independent of any UI framework.
"""
from __future__ import annotations

import time
import random
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from brainworkshop.domain.stimulus_generator import (
    compute_jaeggi_sequence,
    generate_variable_nback_sequence,
    generate_base_stimuli,
    generate_arithmetic_operand,
    apply_nback_matching,
    apply_static_defaults,
    choose_arithmetic_operation,
)
from brainworkshop.domain.match_checker import calculate_session_score

if TYPE_CHECKING:
    from brainworkshop.models.mode import Mode
    from brainworkshop.models.stats import Stats


class GameSession:
    """Core game session state machine - platform independent.

    This class manages the complete lifecycle of an N-back training session,
    including trial progression, stimulus generation, input tracking, and
    scoring. It's independent of any specific rendering or audio technology.

    The session uses a tick-based timing system where each trial progresses
    through phases:
    - Tick 1: New stimulus appears, previous input saved
    - Tick 6: Stimulus disappears
    - Tick (ticks_per_trial - 2): Feedback displayed
    - Tick (ticks_per_trial): Reset for next trial

    Attributes:
        mode: Mode configuration object
        stats: Statistics tracking object
        cfg: Configuration object
        started: Whether session is running
        paused: Whether session is paused
        trial_number: Current trial (1-based)
        trial_starttime: Timestamp when current trial started
        show_missed: Whether to show missed matches feedback
    """

    def __init__(
        self,
        mode: Mode,
        stats: Stats,
        cfg: Any,
    ) -> None:
        """Initialize game session.

        Args:
            mode: Game mode configuration
            stats: Statistics tracker
            cfg: Configuration object
        """
        self.mode = mode
        self.stats = stats
        self.cfg = cfg

        # Callbacks for external effects (UI, audio, etc.)
        self.on_stimulus_generated: Optional[Callable] = None
        self.on_trial_start: Optional[Callable] = None
        self.on_trial_end: Optional[Callable] = None
        self.on_session_end: Optional[Callable] = None
        self.on_feedback_show: Optional[Callable] = None
        self.on_stimulus_hide: Optional[Callable] = None

        # Session state
        self.started = False
        self.paused = False
        self.trial_starttime = 0.0

        # Sound sets and visual indices (set by start())
        self.sound_mode = 'none'
        self.sound2_mode = 'none'
        self.letters: List[str] = []
        self.letters2: List[str] = []
        self.image_indices: List[int] = []

    def start(
        self,
        available_audio_sets: List[str],
        available_audio2_sets: List[str],
    ) -> None:
        """Initialize and start a new session.

        Args:
            available_audio_sets: List of available primary audio set names
            available_audio2_sets: List of available secondary audio set names
        """
        # Initialize timing
        self.mode.tick = -9  # 1-second delay before first trial
        self.mode.tick -= 5 * (self.mode.flags[self.mode.mode]['multi'] - 1)

        if self.cfg.MULTI_MODE == 'image':
            self.mode.tick -= 5 * (self.mode.flags[self.mode.mode]['multi'] - 1)

        # Initialize session counters
        self.mode.session_number += 1
        self.mode.trial_number = 0
        self.started = True
        self.mode.started = True
        self.paused = False
        self.mode.paused = False

        # Randomly select audio sets
        self.sound_mode = random.choice(available_audio_sets)
        self.sound2_mode = random.choice(available_audio2_sets)
        self.mode.sound_mode = self.sound_mode
        self.mode.sound2_mode = self.sound2_mode

        # Generate variable N-back sequence if enabled
        if self.cfg.VARIABLE_NBACK:
            self.mode.variable_list = generate_variable_nback_sequence(
                self.mode.back,
                self.mode.num_trials_total
            )

        # Generate Jaeggi sequence if enabled
        if self.cfg.JAEGGI_MODE:
            self.mode.bt_sequence = compute_jaeggi_sequence(
                self.mode.back,
                self.mode.num_trials_total
            )

        # Initialize statistics
        self.stats.initialize_session()

        # Notify external systems
        if self.on_trial_start:
            self.on_trial_start()

    def update(self, dt: float) -> None:
        """Update game state for one tick.

        This is called at regular intervals (default 10Hz) to advance the
        session through its phases.

        Args:
            dt: Delta time since last update (typically 0.1 seconds)
        """
        if not self.started or self.paused:
            return

        # Handle self-paced mode timing
        if (not self.mode.flags[self.mode.mode]['selfpaced'] or
                self.mode.tick > self.mode.ticks_per_trial - 6 or
                self.mode.tick < 5):
            self.mode.tick += 1

        # Start new trial at tick 1
        if self.mode.tick == 1:
            self._start_new_trial()

        # Hide stimulus at appropriate time
        positions_count = len([mod for mod in self.mode.modalities[self.mode.mode]
                              if mod.startswith('position')])
        positions_count = max(0, positions_count - 1)

        if self.mode.tick == (6 + positions_count) or \
           self.mode.tick == self.mode.ticks_per_trial - 1:
            if self.on_stimulus_hide:
                self.on_stimulus_hide()

        # Show feedback at tick (ticks_per_trial - 2)
        if self.mode.tick == self.mode.ticks_per_trial - 2:
            self.mode.tick = 0
            self.mode.show_missed = True
            if self.on_feedback_show:
                self.on_feedback_show()

        # Reset tick at trial end
        if self.mode.tick == self.mode.ticks_per_trial:
            self.mode.tick = 0

    def _start_new_trial(self) -> None:
        """Internal: Start a new trial."""
        self.mode.show_missed = False

        # Save previous trial's input
        if self.mode.trial_number > 0:
            self.stats.save_input(self.mode)

        # Increment trial
        self.mode.trial_number += 1
        self.trial_starttime = time.time()
        self.mode.trial_starttime = self.trial_starttime

        # Check if session complete
        if self.mode.trial_number > self.mode.num_trials_total:
            self.end()
            return

        # Generate new stimulus
        self._generate_stimulus()

        # Reset inputs
        self._reset_input()

        # Notify trial start
        if self.on_trial_start:
            self.on_trial_start()

    def _generate_stimulus(self) -> None:
        """Internal: Generate stimulus for current trial.

        This is the core stimulus generation logic extracted from the
        original generate_stimulus() function.
        """
        # Generate base random stimuli
        stimuli = generate_base_stimuli(
            self.mode.modalities[self.mode.mode],
            self.mode.flags[self.mode.mode]['multi']
        )

        # Generate arithmetic operand
        operations = choose_arithmetic_operation(
            self.cfg.ARITHMETIC_USE_ADDITION,
            self.cfg.ARITHMETIC_USE_SUBTRACTION,
            self.cfg.ARITHMETIC_USE_MULTIPLICATION,
            self.cfg.ARITHMETIC_USE_DIVISION
        )
        self.mode.current_operation = operations

        # Determine min/max for arithmetic
        if self.cfg.ARITHMETIC_USE_NEGATIVES:
            min_number = 0 - self.cfg.ARITHMETIC_MAX_NUMBER
        else:
            min_number = 0
        max_number = self.cfg.ARITHMETIC_MAX_NUMBER

        # Generate arithmetic number with special handling for division
        previous_result = None
        if self.mode.current_operation == 'divide' and \
           'arithmetic' in self.mode.modalities[self.mode.mode] and \
           len(self.stats.session['position1']) >= self.mode.back:
            previous_result = self.stats.session['numbers'][
                self.mode.trial_number - self.mode.back - 1
            ]

        stimuli['number'] = generate_arithmetic_operand(
            self.mode.current_operation,
            min_number,
            max_number,
            self.cfg.ARITHMETIC_ACCEPTABLE_DECIMALS,
            previous_result
        )

        # Determine real N-back for this trial
        real_back = self._get_real_back()

        # Apply N-back matching logic
        if self.mode.modalities[self.mode.mode] != ['arithmetic'] and \
           self.mode.trial_number > self.mode.back:
            stimuli = apply_nback_matching(
                stimuli,
                self.stats.session,
                self.mode.trial_number,
                real_back,
                self.mode.modalities[self.mode.mode],
                self.cfg.CHANCE_OF_GUARANTEED_MATCH,
                self.cfg.CHANCE_OF_INTERFERENCE,
                self.mode.flags[self.mode.mode]['multi'],
                debug=False  # Could be cfg.DEBUG if needed
            )

        # Apply static defaults for inactive modalities
        stimuli = apply_static_defaults(
            stimuli,
            self.mode.modalities[self.mode.mode],
            self.cfg.VISUAL_COLORS[0] if hasattr(self.cfg, 'VISUAL_COLORS') else 1
        )

        # Store current stimuli
        self.mode.current_stim = stimuli

        # Notify stimulus generated
        if self.on_stimulus_generated:
            self.on_stimulus_generated(stimuli)

    def _get_real_back(self) -> int:
        """Get the effective N-back level for current trial.

        Handles crab mode and variable N-back.

        Returns:
            Effective N-back level
        """
        if self.mode.flags[self.mode.mode]['crab'] == 1:
            return 1 + 2 * ((self.mode.trial_number - 1) % self.mode.back)
        elif self.cfg.VARIABLE_NBACK:
            return self.mode.variable_list[self.mode.trial_number - self.mode.back - 1]
        else:
            return self.mode.back

    def _reset_input(self) -> None:
        """Internal: Reset all player inputs."""
        for k in list(self.mode.inputs):
            self.mode.inputs[k] = False
            self.mode.input_rts[k] = 0.0

    def register_input(self, modality: str, timestamp: float = None) -> None:
        """Register player input for a modality.

        Args:
            modality: Modality name (position1, audio, color, etc.)
            timestamp: Time of input (defaults to current time)
        """
        if timestamp is None:
            timestamp = time.time()

        if modality in self.mode.inputs:
            self.mode.inputs[modality] = True
            self.mode.input_rts[modality] = timestamp - self.trial_starttime

    def end(self, cancelled: bool = False) -> None:
        """End the current session.

        Args:
            cancelled: If True, session was cancelled (don't save stats)
        """
        if cancelled:
            self.mode.session_number -= 1
        else:
            self.stats.sessions_today += 1

        self.started = False
        self.mode.started = False
        self.paused = False
        self.mode.paused = False

        # Reset inputs
        self._reset_input()

        # Calculate scores if not cancelled
        if not cancelled:
            scores = calculate_session_score(
                self.stats.session,
                self.mode.back,
                self.mode.modalities[self.mode.mode],
                self.mode.trial_number - 1  # Actual trials completed
            )

            # Notify session end with scores
            if self.on_session_end:
                self.on_session_end(scores, cancelled)
        else:
            # Notify session cancelled
            if self.on_session_end:
                self.on_session_end({}, cancelled)

    def pause(self) -> None:
        """Pause the session."""
        self.paused = True
        self.mode.paused = True

    def resume(self) -> None:
        """Resume the session."""
        self.paused = False
        self.mode.paused = False
