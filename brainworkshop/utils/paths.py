"""Path and directory utilities."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

# Default folder names
FOLDER_RES = 'res'
FOLDER_DATA = 'data'


def get_argv(arg: str) -> Optional[str]:
    """Get command line argument value following the specified argument."""
    if arg in sys.argv:
        index = sys.argv.index(arg)
        if index + 1 < len(sys.argv):
            return sys.argv[index + 1]
        else:
            print(f"ERROR: Expected an argument following {arg}")
            exit(1)
    return None


def main_is_frozen() -> bool:
    """Check if running as frozen executable (py2exe)."""
    return hasattr(sys, "frozen")  # py2exe


def get_main_dir() -> str:
    """Get main application directory."""
    if main_is_frozen():
        return str(Path(sys.executable).parent)
    return sys.path[0]


def get_settings_path(name: str) -> str:
    """Get a directory to save user preferences.
    Copied from pyglet.resource so we don't have to load that module
    (which recursively indexes . on loading -- wtf?)."""
    if sys.platform in ('cygwin', 'win32'):
        if 'APPDATA' in os.environ:
            return str(Path(os.environ['APPDATA']) / name)
        else:
            return str(Path(f'~/{name}').expanduser())
    elif sys.platform == 'darwin':
        return str(Path(f'~/Library/Application Support/{name}').expanduser())
    else:  # on *nix, we want it to be lowercase and without spaces (~/.brainworkshop/data)
        return str(Path(f'~/.{name.lower().replace(" ", "")}').expanduser())


def get_data_dir() -> str:
    """Get data directory path from args or default settings."""
    rtrn = get_argv('--datadir')
    if rtrn:
        return rtrn
    else:
        return str(Path(get_settings_path('Brain Workshop')) / FOLDER_DATA)


def get_res_dir() -> str:
    """Get resources directory path from args or default location."""
    rtrn = get_argv('--resdir')
    if rtrn:
        return rtrn
    else:
        return str(Path(get_main_dir()) / FOLDER_RES)
