"""Pure stimulus generation logic - platform independent.

This module contains the core algorithms for generating N-back stimuli,
including standard randomization and Jaeggi-mode sequence generation.
"""
from __future__ import annotations

import random
from decimal import Decimal
from typing import Any, Dict, List, Tuple


def compute_jaeggi_sequence(n_back: int, num_trials: int) -> List[List[int]]:
    """Generate Brain Training sequence for Jaeggi mode.

    Generates predetermined stimulus sequences with exactly 6 position matches,
    6 audio matches, and 2 simultaneous matches per session, following the
    original Jaeggi study protocol. This creates more predictable and less
    random sequences compared to the default BW generation model.

    Args:
        n_back: N-back level (how many trials back to remember)
        num_trials: Total number of trials in session

    Returns:
        List containing two sublists: [position_sequence, audio_sequence]
        Each sequence is a list of integers 1-8 representing stimuli
    """
    bt_sequence = [[], []]
    for x in range(0, num_trials):
        bt_sequence[0].append(0)
        bt_sequence[1].append(0)

    for x in range(0, n_back):
        bt_sequence[0][x] = random.randint(1, 8)
        bt_sequence[1][x] = random.randint(1, 8)

    position = 0
    audio = 0
    both = 0

    # Brute force it - keep generating until we get exactly 6+6+2 matches
    while True:
        position = 0
        for x in range(n_back, num_trials):
            bt_sequence[0][x] = random.randint(1, 8)
            if bt_sequence[0][x] == bt_sequence[0][x - n_back]:
                position += 1
        if position != 6:
            continue
        while True:
            audio = 0
            for x in range(n_back, num_trials):
                bt_sequence[1][x] = random.randint(1, 8)
                if bt_sequence[1][x] == bt_sequence[1][x - n_back]:
                    audio += 1
            if audio == 6:
                break
        both = 0
        for x in range(n_back, num_trials):
            if bt_sequence[0][x] == bt_sequence[0][x - n_back] and \
               bt_sequence[1][x] == bt_sequence[1][x - n_back]:
                both += 1
        if both == 2:
            break

    return bt_sequence


def generate_variable_nback_sequence(n_back: int, num_trials: int) -> List[int]:
    """Generate variable N-back sequence using beta distribution.

    Creates a list of N-back levels that varies within a session, using
    a beta distribution to provide controlled randomness.

    Args:
        n_back: Base N-back level
        num_trials: Total number of trials (minus n_back for warmup)

    Returns:
        List of N-back levels to use for each trial
    """
    variable_list = []
    for index in range(0, num_trials - n_back):
        variable_list.append(int(random.betavariate(n_back / 2.0, 1) * n_back + 1))
    return variable_list


def generate_base_stimuli(
    modalities: List[str],
    multi_mode: int = 1
) -> Dict[str, int]:
    """Generate random base stimuli for all modalities.

    Args:
        modalities: List of modality strings (position1, audio, color, etc.)
        multi_mode: Number of simultaneous stimuli (1-4)

    Returns:
        Dictionary mapping modality names to random stimulus values (1-8)
    """
    stimuli = {}

    # Generate position stimuli without replacement (no collisions)
    positions = random.sample(range(1, 9), 4)
    for s, p in zip(range(1, 5), positions):
        stimuli[f'position{s}'] = p
        stimuli[f'vis{s}'] = random.randint(1, 8)

    # Generate other modalities
    stimuli['color'] = random.randint(1, 8)
    stimuli['vis'] = random.randint(1, 8)
    stimuli['audio'] = random.randint(1, 8)
    stimuli['audio2'] = random.randint(1, 8)

    return stimuli


def generate_arithmetic_operand(
    operation: str,
    min_number: int,
    max_number: int,
    acceptable_decimals: List[float],
    previous_result: int = None
) -> int:
    """Generate operand for arithmetic N-back.

    For division operations, ensures the operand produces acceptable decimals
    when divided with the N-back result.

    Args:
        operation: Arithmetic operation ('add', 'subtract', 'multiply', 'divide')
        min_number: Minimum operand value
        max_number: Maximum operand value
        acceptable_decimals: List of acceptable decimal fractions for division
        previous_result: Previous trial's result for division validation

    Returns:
        Random operand value
    """
    if operation == 'divide' and previous_result is not None:
        # For division, find operands that give acceptable decimals
        possibilities = []
        for x in range(min_number, max_number + 1):
            if x == 0:
                continue
            if previous_result % x == 0:
                possibilities.append(x)
                continue
            frac = Decimal(abs(previous_result)) / Decimal(abs(x))
            if (frac % 1) in map(Decimal, acceptable_decimals):
                possibilities.append(x)

        if possibilities:
            return random.choice(possibilities)

    # Default random selection (or fallback for division)
    number = random.randint(min_number, max_number)
    while number == 0:
        number = random.randint(min_number, max_number)
    return number


def apply_nback_matching(
    current_stim: Dict[str, int],
    session_history: Dict[str, List[int]],
    trial_number: int,
    n_back: int,
    modalities: List[str],
    chance_guaranteed_match: float,
    chance_interference: float,
    multi_mode: int = 1,
    debug: bool = False
) -> Dict[str, int]:
    """Apply N-back matching logic to stimuli.

    Modifies stimuli to create matches or interference based on probability
    settings. This is the core N-back pattern generation logic.

    Args:
        current_stim: Current trial stimuli dictionary
        session_history: All previous trial stimuli
        trial_number: Current trial number (1-based)
        n_back: N-back level
        modalities: Active modalities for this mode
        chance_guaranteed_match: Probability of forcing a match (0-1)
        chance_interference: Probability of forcing interference (0-1)
        multi_mode: Number of simultaneous stimuli
        debug: Enable debug output

    Returns:
        Modified stimuli dictionary with N-back matches applied
    """
    if trial_number <= n_back:
        return current_stim

    positions = [current_stim.get(f'position{i}', 0) for i in range(1, 5)]

    for mod in modalities:
        if mod == 'arithmetic':
            continue

        # Map modality names to current stim keys
        if mod in ('visvis', 'visaudio', 'image'):
            current = 'vis'
        elif mod in ('audiovis', ):
            current = 'audio'
        else:
            current = mod

        # Map modality names to history keys
        if mod in ('visvis', 'audiovis', 'image'):
            back_data = 'vis'
        elif mod in ('visaudio', ):
            back_data = 'audio'
        else:
            back_data = mod

        back = None
        r1, r2 = random.random(), random.random()

        if multi_mode > 1:
            r2 = 3./2. * r2  # 33% chance of multi-stim reversal

        # Apply guaranteed match
        if r1 < chance_guaranteed_match:
            back = n_back

        # Apply interference (n±1 matches)
        elif r2 < chance_interference and n_back > 1:
            back = n_back
            interference = [-1, 1, n_back]
            if back < 3:
                interference = interference[1:]  # for crab mode and 2-back
            random.shuffle(interference)

            for i in interference:
                if trial_number - (n_back + i) - 1 >= 0 and \
                   session_history[back_data][trial_number - (n_back + i) - 1] != \
                   session_history[back_data][trial_number - n_back - 1]:
                    back = n_back + i
                    break

            if back == n_back:
                back = None
            elif debug:
                print(f'Forcing interference for {current}')

        # Apply the match
        if back:
            nback_trial = trial_number - back - 1
            matching_stim = session_history[back_data][nback_trial]

            # Check for collisions in multi-stim mode
            if multi_mode > 1 and mod.startswith('position'):
                potential_conflicts = set(range(1, multi_mode+1)) - set([int(mod[-1])])
                conflict_positions = [positions[i-1] for i in potential_conflicts]

                if matching_stim in conflict_positions:  # Swap 'em
                    i = positions.index(matching_stim)
                    if debug:
                        print(f"moving position{i+1} from {positions[i]} to {current_stim[current]} for {current}")
                    current_stim[f'position{i+1}'] = current_stim[current]
                    positions[i] = current_stim[current]

                positions[int(current[-1])-1] = matching_stim

            if debug:
                print(f"setting {current} to {matching_stim}")
            current_stim[current] = matching_stim

    # Multi-stim reversal interference
    if multi_mode > 1:
        if random.random() < chance_interference / 3.:
            mod = 'position'
            if 'vis1' in modalities and random.random() < .5:
                mod = 'vis'
            offset = random.choice(range(1, multi_mode))

            for i in range(multi_mode):
                current_stim[f'{mod}{i+1}'] = session_history[f'{mod}{((i+offset)%multi_mode) + 1}'][trial_number - n_back - 1]
                if mod == 'position':
                    positions[i] = current_stim[f'{mod}{i+1}']

    return current_stim


def apply_static_defaults(
    stimuli: Dict[str, int],
    modalities: List[str],
    default_color: int = 1
) -> Dict[str, int]:
    """Apply static default values for inactive modalities.

    Args:
        stimuli: Stimuli dictionary to modify
        modalities: Active modalities list
        default_color: Default color index to use

    Returns:
        Modified stimuli dictionary with defaults applied
    """
    # Default position is 0 (center)
    # Default color is 1 (red) or 2 (black)
    # Default vis is 0 (square)
    # Audio is never static so it doesn't have a default

    if 'color' not in modalities:
        stimuli['color'] = default_color

    if 'position1' not in modalities:
        stimuli['position1'] = 0

    if not set(['visvis', 'arithmetic', 'image']).intersection(modalities):
        stimuli['vis'] = 0

    return stimuli


def choose_arithmetic_operation(
    use_addition: bool,
    use_subtraction: bool,
    use_multiplication: bool,
    use_division: bool
) -> str:
    """Randomly choose an arithmetic operation based on enabled operations.

    Args:
        use_addition: Whether addition is enabled
        use_subtraction: Whether subtraction is enabled
        use_multiplication: Whether multiplication is enabled
        use_division: Whether division is enabled

    Returns:
        Operation string: 'add', 'subtract', 'multiply', or 'divide'
    """
    operations = []
    if use_addition:
        operations.append('add')
    if use_subtraction:
        operations.append('subtract')
    if use_multiplication:
        operations.append('multiply')
    if use_division:
        operations.append('divide')

    if not operations:
        operations = ['add']  # Fallback

    return random.choice(operations)
