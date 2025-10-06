"""Debug and error utilities."""
from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import Optional

# Global DEBUG flag - will be set by main module
DEBUG = False


def debug_msg(msg: str | Exception) -> None:
    """Print debug message if DEBUG mode is enabled."""
    if DEBUG:
        if isinstance(msg, Exception):
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = Path(exc_tb.tb_frame.f_code.co_filename).name
            print(f'debug: {msg} Line {exc_tb.tb_lineno}')
        else:
            print(f'debug: {msg}')


def error_msg(msg: str, e: Optional[Exception] = None) -> None:
    """Print error message with optional exception details."""
    if DEBUG and e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = Path(exc_tb.tb_frame.f_code.co_filename).name
        print(f"ERROR: {msg}\n\t{e} Line {exc_tb.tb_lineno}")
    else:
        print(f"ERROR: {msg}")


def quit_with_error(message: str = '', postmessage: str = '', quit: bool = True, trace: bool = True) -> None:
    """Print error message and optionally exit."""
    if message:
        sys.stderr.write(message + '\n')
    if trace:
        sys.stderr.write("Full text of error:\n")
        traceback.print_exc()
    if postmessage:
        sys.stderr.write('\n\n' + postmessage)
    if quit:
        sys.exit(1)
