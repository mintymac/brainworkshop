"""Pure N-back match checking and scoring logic - platform independent.

This module contains algorithms for validating player inputs against
N-back stimuli and calculating performance scores.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


def check_position_match(
    session_history: Dict[str, List[int]],
    trial_number: int,
    n_back: int,
    position_key: str = 'position1'
) -> bool:
    """Check if current position matches N-back position.

    Args:
        session_history: All trial data
        trial_number: Current trial number (1-based)
        n_back: N-back level
        position_key: Position key to check (position1, position2, etc.)

    Returns:
        True if current position matches N-back position
    """
    if trial_number <= n_back:
        return False

    current_idx = trial_number - 1
    nback_idx = trial_number - n_back - 1

    if nback_idx < 0 or current_idx >= len(session_history[position_key]):
        return False

    return session_history[position_key][current_idx] == \
           session_history[position_key][nback_idx]


def check_audio_match(
    session_history: Dict[str, List[int]],
    trial_number: int,
    n_back: int,
    audio_key: str = 'audio'
) -> bool:
    """Check if current audio matches N-back audio.

    Args:
        session_history: All trial data
        trial_number: Current trial number (1-based)
        n_back: N-back level
        audio_key: Audio key to check (audio, audio2)

    Returns:
        True if current audio matches N-back audio
    """
    if trial_number <= n_back:
        return False

    current_idx = trial_number - 1
    nback_idx = trial_number - n_back - 1

    if nback_idx < 0 or current_idx >= len(session_history[audio_key]):
        return False

    return session_history[audio_key][current_idx] == \
           session_history[audio_key][nback_idx]


def check_color_match(
    session_history: Dict[str, List[int]],
    trial_number: int,
    n_back: int
) -> bool:
    """Check if current color matches N-back color.

    Args:
        session_history: All trial data
        trial_number: Current trial number (1-based)
        n_back: N-back level

    Returns:
        True if current color matches N-back color
    """
    if trial_number <= n_back:
        return False

    current_idx = trial_number - 1
    nback_idx = trial_number - n_back - 1

    if nback_idx < 0 or current_idx >= len(session_history['color']):
        return False

    return session_history['color'][current_idx] == \
           session_history['color'][nback_idx]


def check_image_match(
    session_history: Dict[str, List[int]],
    trial_number: int,
    n_back: int
) -> bool:
    """Check if current image matches N-back image.

    Args:
        session_history: All trial data
        trial_number: Current trial number (1-based)
        n_back: N-back level

    Returns:
        True if current image matches N-back image
    """
    if trial_number <= n_back:
        return False

    current_idx = trial_number - 1
    nback_idx = trial_number - n_back - 1

    if nback_idx < 0 or current_idx >= len(session_history['image']):
        return False

    return session_history['image'][current_idx] == \
           session_history['image'][nback_idx]


def check_combination_match(
    session_history: Dict[str, List[int]],
    trial_number: int,
    n_back: int,
    combination_type: str
) -> bool:
    """Check combination modality matches (visvis, visaudio, audiovis).

    Args:
        session_history: All trial data
        trial_number: Current trial number (1-based)
        n_back: N-back level
        combination_type: 'visvis', 'visaudio', or 'audiovis'

    Returns:
        True if combination matches
    """
    if trial_number <= n_back:
        return False

    current_idx = trial_number - 1
    nback_idx = trial_number - n_back - 1

    if nback_idx < 0:
        return False

    if combination_type == 'visvis':
        # Visual and visual match
        return (session_history['vis'][current_idx] ==
                session_history['vis'][nback_idx])
    elif combination_type == 'visaudio':
        # Visual and audio match
        return (session_history['vis'][current_idx] ==
                session_history['audio'][nback_idx])
    elif combination_type == 'audiovis':
        # Audio and visual match
        return (session_history['audio'][current_idx] ==
                session_history['vis'][nback_idx])

    return False


def check_arithmetic_match(
    session_history: Dict[str, List],
    trial_number: int,
    n_back: int,
    player_answer: int
) -> bool:
    """Check if arithmetic answer matches N-back result.

    Computes the arithmetic result from N-back trial and compares
    to player's answer.

    Args:
        session_history: All trial data including 'numbers' and 'operation'
        trial_number: Current trial number (1-based)
        n_back: N-back level
        player_answer: Player's computed answer

    Returns:
        True if player's answer matches N-back arithmetic result
    """
    if trial_number <= n_back:
        return False

    nback_idx = trial_number - n_back - 1
    current_idx = trial_number - 1

    if nback_idx < 0 or nback_idx >= len(session_history['numbers']):
        return False
    if current_idx >= len(session_history['numbers']):
        return False

    # Get the number from N-back trial and operation from current trial
    nback_number = session_history['numbers'][nback_idx]
    current_number = session_history['numbers'][current_idx]
    operation = session_history['operation'][current_idx]

    # Compute expected result
    if operation == 'add':
        expected = nback_number + current_number
    elif operation == 'subtract':
        expected = nback_number - current_number
    elif operation == 'multiply':
        expected = nback_number * current_number
    elif operation == 'divide':
        if current_number == 0:
            return False
        expected = float(nback_number) / float(current_number)
    else:
        return False

    # For division, allow some tolerance
    if operation == 'divide':
        return abs(player_answer - expected) < 0.01

    return player_answer == expected


def calculate_modality_score(
    session_history: Dict[str, List],
    n_back: int,
    modality: str,
    num_trials: int
) -> Tuple[int, int, float]:
    """Calculate score for a single modality.

    Args:
        session_history: All trial data
        n_back: N-back level
        modality: Modality name (position1, audio, color, etc.)
        num_trials: Total number of trials

    Returns:
        Tuple of (hits, possible_hits, percentage)
    """
    hits = 0
    possible_hits = 0

    for trial in range(1, num_trials + 1):
        if trial <= n_back:
            continue

        current_idx = trial - 1
        nback_idx = trial - n_back - 1

        if nback_idx < 0:
            continue

        # Determine if match exists
        is_match = False
        player_input = False

        if modality.startswith('position'):
            if current_idx < len(session_history[modality]):
                is_match = (session_history[modality][current_idx] ==
                           session_history[modality][nback_idx])
                player_input = session_history.get(f'{modality}_input', [False])[current_idx]

        elif modality == 'audio' or modality == 'audio2':
            if current_idx < len(session_history[modality]):
                is_match = (session_history[modality][current_idx] ==
                           session_history[modality][nback_idx])
                player_input = session_history.get(f'{modality}_input', [False])[current_idx]

        elif modality == 'color':
            if current_idx < len(session_history['color']):
                is_match = (session_history['color'][current_idx] ==
                           session_history['color'][nback_idx])
                player_input = session_history.get('color_input', [False])[current_idx]

        elif modality == 'image':
            if current_idx < len(session_history['image']):
                is_match = (session_history['image'][current_idx] ==
                           session_history['image'][nback_idx])
                player_input = session_history.get('image_input', [False])[current_idx]

        elif modality in ('visvis', 'visaudio', 'audiovis'):
            player_input = session_history.get(f'{modality}_input', [False])[current_idx]
            is_match = check_combination_match(session_history, trial, n_back, modality)

        # Score: correct if (match and pressed) or (no match and not pressed)
        if is_match == player_input:
            hits += 1
        possible_hits += 1

    percentage = (hits / possible_hits * 100) if possible_hits > 0 else 0
    return hits, possible_hits, percentage


def calculate_session_score(
    session_history: Dict[str, List],
    n_back: int,
    modalities: List[str],
    num_trials: int
) -> Dict[str, float]:
    """Calculate overall session score across all modalities.

    Args:
        session_history: All trial data
        n_back: N-back level
        modalities: Active modalities for this mode
        num_trials: Total number of trials

    Returns:
        Dictionary mapping modality names to percentage scores
    """
    scores = {}
    total_hits = 0
    total_possible = 0

    # Initialize all modalities to 0
    for mod in ['position1', 'position2', 'position3', 'position4',
                'audio', 'audio2', 'color', 'image',
                'visvis', 'visaudio', 'audiovis', 'arithmetic',
                'vis1', 'vis2', 'vis3', 'vis4']:
        scores[mod] = 0.0

    # Calculate score for each active modality
    for modality in modalities:
        if modality == 'arithmetic':
            # Arithmetic requires special handling
            hits, possible, percentage = calculate_arithmetic_score(
                session_history, n_back, num_trials
            )
        else:
            hits, possible, percentage = calculate_modality_score(
                session_history, n_back, modality, num_trials
            )

        scores[modality] = percentage
        total_hits += hits
        total_possible += possible

    # Calculate overall percentage
    if total_possible > 0:
        scores['overall'] = total_hits / total_possible * 100
    else:
        scores['overall'] = 0.0

    return scores


def calculate_arithmetic_score(
    session_history: Dict[str, List],
    n_back: int,
    num_trials: int
) -> Tuple[int, int, float]:
    """Calculate arithmetic modality score.

    Args:
        session_history: All trial data
        n_back: N-back level
        num_trials: Total number of trials

    Returns:
        Tuple of (hits, possible_hits, percentage)
    """
    hits = 0
    possible_hits = 0

    for trial in range(1, num_trials + 1):
        if trial <= n_back:
            continue

        current_idx = trial - 1
        if current_idx >= len(session_history.get('arithmetic_input', [])):
            continue

        player_answer = session_history['arithmetic_input'][current_idx]
        is_correct = check_arithmetic_match(session_history, trial, n_back, player_answer)

        if is_correct:
            hits += 1
        possible_hits += 1

    percentage = (hits / possible_hits * 100) if possible_hits > 0 else 0
    return hits, possible_hits, percentage
