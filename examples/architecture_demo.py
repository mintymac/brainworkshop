"""Demo showing the new hexagonal architecture in action.

This example demonstrates how the refactored components will work together
using dependency injection and port/adapter pattern.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from brainworkshop.models.config import dotdict
from brainworkshop.models.mode import Mode
from brainworkshop.utils.paths import get_data_dir, get_res_dir
from brainworkshop.utils.debug import debug_msg, error_msg


def demo_config():
    """Demo the dotdict configuration model."""
    print("\n=== Configuration Model Demo ===")

    config = dotdict({
        'GAME_MODE': 2,
        'BACK_DEFAULT': 2,
        'TICKS_DEFAULT': 30,
        'NUM_TRIALS': 20,
        'NUM_TRIALS_FACTOR': 5,
        'NUM_TRIALS_EXPONENT': 2,
        'MANUAL': False,
        'SKIP_TITLE_SCREEN': False,
        'HIDE_TEXT': False,
    })

    print(f"Config created: {len(config)} settings")
    print(f"  Game mode: {config.GAME_MODE}")
    print(f"  Default n-back: {config.BACK_DEFAULT}")
    print(f"  Can access via dict: {config['GAME_MODE']}")
    print(f"  Can access via attr: {config.GAME_MODE}")

    return config


def demo_mode(config):
    """Demo the Mode model."""
    print("\n=== Mode Model Demo ===")

    # Create mode with dependency injection
    mode = Mode(config, translation_func=lambda x: x)

    print(f"Mode initialized: {mode.short_name()}")
    print(f"  N-back level: {mode.back}")
    print(f"  Ticks per trial: {mode.ticks_per_trial}")
    print(f"  Total trials: {mode.num_trials_total}")
    print(f"  Available modes: {len(mode.short_mode_names)}")

    # Show some mode names
    print("\n  Sample modes:")
    for mode_id in [2, 3, 7, 10, 11]:
        short = mode.short_mode_names[mode_id]
        long = mode.long_mode_names[mode_id]
        modalities = ', '.join(mode.modalities[mode_id])
        print(f"    {short:4} - {long:20} [{modalities}]")

    return mode


def demo_paths():
    """Demo the path utilities."""
    print("\n=== Path Utilities Demo ===")

    data_dir = get_data_dir()
    res_dir = get_res_dir()

    print(f"Data directory: {data_dir}")
    print(f"Resources directory: {res_dir}")


def demo_ports():
    """Demo the port interfaces."""
    print("\n=== Port Interfaces Demo ===")

    from brainworkshop.ports.renderer import IRenderer
    from brainworkshop.ports.audio_player import IAudioPlayer
    from brainworkshop.ports.stats_repository import IStatsRepository

    print("Port interfaces defined:")
    print(f"  IRenderer: {', '.join([m for m in dir(IRenderer) if not m.startswith('_')])}")
    print(f"  IAudioPlayer: {', '.join([m for m in dir(IAudioPlayer) if not m.startswith('_')])}")
    print(f"  IStatsRepository: {', '.join([m for m in dir(IStatsRepository) if not m.startswith('_')])}")

    print("\nThese interfaces allow swapping implementations:")
    print("  - Desktop: Pyglet renderer, Pyglet audio, File storage")
    print("  - Web: Canvas renderer, Web Audio API, LocalStorage/IndexedDB")
    print("  - Mobile: Native renderer, Native audio, SQLite storage")


def main():
    """Run all demos."""
    print("="*60)
    print("BrainWorkshop Hexagonal Architecture Demo")
    print("="*60)

    config = demo_config()
    mode = demo_mode(config)
    demo_paths()
    demo_ports()

    print("\n" + "="*60)
    print("Phase 1 Complete: Models Extracted, Ports Defined")
    print("Next: Implement adapters and wire dependencies")
    print("="*60)


if __name__ == '__main__':
    main()
